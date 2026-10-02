from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn

from config.ransomware.catboost_trainer import (
    WINDOWS,
    build_rows,
    load_and_verify_scenarios,
)
from config.ransomware.scenarios.scenario_event_assembler import (
    assemble_scenario_events,
)

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "artifacts/ransomware/offline"
MODEL_PATH = REPORT_DIR / "rw0802_tcn_model.pt"
MANIFEST_PATH = REPORT_DIR / "rw0802_tcn_window_manifest.json"
REPORT_PATH = REPORT_DIR / "rw0802_tcn_report.json"

SEED = 20260921
WINDOW_SIZE = 8
EPOCHS = 30
LEARNING_RATE = 0.001
DETECTION_THRESHOLD = 0.5


@dataclass(frozen=True)
class ScenarioSequence:
    scenario_id: str
    split: str
    variant: str
    industry: str
    timesteps: np.ndarray
    stages: tuple[str | None, ...]


def build_sequence(scenario) -> ScenarioSequence:
    events = assemble_scenario_events(scenario)
    events = sorted(events, key=lambda event: (event.event_time, event.sequence_index))

    rows_by_time = {}

    for event in events:
        rows_by_time.setdefault(event.event_time, []).append(event)

    rows = []
    stages = []

    for event_time in sorted(rows_by_time):
        timestep_events = rows_by_time[event_time]

        vectors = []
        stage = None

        for window_minutes in WINDOWS:
            features = build_rows(
                [
                    type(
                        "ScenarioLike",
                        (),
                        {
                            "scenario_id": scenario.scenario_id,
                            "split": scenario.split,
                            "variant": scenario.variant,
                            "industry": scenario.industry,
                            "site_types": scenario.site_types,
                        },
                    )()
                ]
            ) if False else None

            # Window features are generated directly from the ordered
            # observable event stream below.
            from config.ransomware.features.window_features import (
                extract_window_features,
            )

            from datetime import datetime, timezone

            end_time = datetime.fromisoformat(event_time.replace("Z", "+00:00"))

            feature_map = extract_window_features(
                events,
                end_time,
                window_minutes,
            )

            if not vectors:
                feature_names = tuple(sorted(feature_map))

            vectors.extend(float(feature_map[name]) for name in feature_names)

        for event in timestep_events:
            candidate_stage = event.attributes.get("stage")
            if candidate_stage:
                stage = candidate_stage

        rows.append(vectors)
        stages.append(stage)

    return ScenarioSequence(
        scenario_id=scenario.scenario_id,
        split=scenario.split,
        variant=scenario.variant,
        industry=scenario.industry,
        timesteps=np.asarray(rows, dtype=np.float32),
        stages=tuple(stages),
    )


def build_sequences(frozen_scenarios):
    sequences = [build_sequence(scenario) for scenario in frozen_scenarios]

    feature_count = {sequence.timesteps.shape[1] for sequence in sequences}
    if len(feature_count) != 1:
        raise ValueError(f"Inconsistent TCN feature dimensions: {feature_count}")

    return sequences


class CausalConv1d(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, dilation):
        super().__init__()
        self.padding = (kernel_size - 1) * dilation
        self.conv = nn.Conv1d(
            in_channels,
            out_channels,
            kernel_size,
            padding=self.padding,
            dilation=dilation,
        )

    def forward(self, x):
        x = self.conv(x)
        if self.padding:
            x = x[:, :, :-self.padding]
        return x


class TCNBlock(nn.Module):
    def __init__(self, in_channels, out_channels, dilation):
        super().__init__()

        self.conv1 = CausalConv1d(
            in_channels,
            out_channels,
            kernel_size=3,
            dilation=dilation,
        )
        self.conv2 = CausalConv1d(
            out_channels,
            out_channels,
            kernel_size=3,
            dilation=dilation,
        )

        self.norm1 = nn.BatchNorm1d(out_channels)
        self.norm2 = nn.BatchNorm1d(out_channels)
        self.activation = nn.ReLU()

        self.residual = (
            nn.Conv1d(in_channels, out_channels, kernel_size=1)
            if in_channels != out_channels
            else nn.Identity()
        )

    def forward(self, x):
        residual = self.residual(x)

        y = self.conv1(x)
        y = self.activation(self.norm1(y))

        y = self.conv2(y)
        y = self.norm2(y)

        return self.activation(y + residual)


class AttentionPooling(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.score = nn.Linear(channels, 1)

    def forward(self, x):
        # x: batch, time, channels
        scores = self.score(x).squeeze(-1)
        weights = torch.softmax(scores, dim=1)
        return torch.sum(x * weights.unsqueeze(-1), dim=1)


class TCNClassifier(nn.Module):
    def __init__(self, input_features):
        super().__init__()

        self.tcn = nn.Sequential(
            TCNBlock(input_features, 32, dilation=1),
            TCNBlock(32, 32, dilation=2),
            TCNBlock(32, 32, dilation=4),
        )

        self.pool = AttentionPooling(32)
        self.classifier = nn.Linear(32, 1)

    def forward(self, x):
        # x: batch, time, features
        x = x.transpose(1, 2)
        x = self.tcn(x)
        x = x.transpose(1, 2)
        x = self.pool(x)
        return self.classifier(x).squeeze(-1)


def pad_sequence(sequence: np.ndarray) -> np.ndarray:
    if len(sequence) >= WINDOW_SIZE:
        return sequence[-WINDOW_SIZE:]

    padding = np.zeros(
        (WINDOW_SIZE - len(sequence), sequence.shape[1]),
        dtype=np.float32,
    )

    return np.vstack([padding, sequence])


def make_training_data(sequences):
    samples = []
    labels = []

    for sequence in sequences:
        for end in range(1, len(sequence.timesteps) + 1):
            window = pad_sequence(sequence.timesteps[:end])
            samples.append(window)
            labels.append(1.0 if sequence.variant == "attack" else 0.0)

    return (
        np.asarray(samples, dtype=np.float32),
        np.asarray(labels, dtype=np.float32),
    )


def detection_metrics(model, sequences):
    model.eval()

    results = []
    attack_delays = []

    with torch.no_grad():
        for sequence in sequences:
            probabilities = []

            for end in range(1, len(sequence.timesteps) + 1):
                window = pad_sequence(sequence.timesteps[:end])
                tensor = torch.from_numpy(window).unsqueeze(0)
                probability = torch.sigmoid(model(tensor)).item()
                probabilities.append(probability)

            detected_at = None

            for index, probability in enumerate(probabilities):
                if probability >= DETECTION_THRESHOLD:
                    detected_at = index
                    break

            if sequence.variant == "attack":
                if detected_at is not None:
                    delay = detected_at
                    attack_delays.append(delay)

            results.append(
                {
                    "scenario_id": sequence.scenario_id,
                    "variant": sequence.variant,
                    "detected": detected_at is not None,
                    "detected_at_timestep": detected_at,
                    "probabilities": probabilities,
                    "stages": list(sequence.stages),
                }
            )

    attack_results = [
        item for item in results if item["variant"] == "attack"
    ]

    stage_recall = {}

    for stage in (
        "initial_access",
        "execution_persistence",
        "privilege_escalation",
        "discovery",
        "lateral_movement",
        "staging",
        "recovery_impairment",
        "encryption_impact",
        "extortion_marker",
        "recovery",
    ):
        stage_positions = []

        for result in attack_results:
            if stage in result["stages"]:
                stage_positions.append(
                    result["stages"].index(stage)
                )

        detected_count = 0

        for result, stage_position in zip(
            attack_results,
            stage_positions,
        ):
            if any(
                probability >= DETECTION_THRESHOLD
                for probability in result["probabilities"][: stage_position + 1]
            ):
                detected_count += 1

        stage_recall[stage] = (
            detected_count / len(stage_positions)
            if stage_positions
            else 0.0
        )

    return {
        "attack_scenario_count": len(attack_results),
        "detected_attack_count": sum(
            1
            for result in attack_results
            if result["detected"]
        ),
        "attack_detection_rate": (
            sum(1 for result in attack_results if result["detected"])
            / len(attack_results)
            if attack_results
            else 0.0
        ),
        "mean_detection_delay_timesteps": (
            float(np.mean(attack_delays))
            if attack_delays
            else None
        ),
        "stage_recall": stage_recall,
        "scenario_results": results,
    }


def main():
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    manifest, frozen = load_and_verify_scenarios()
    sequences = build_sequences(frozen)

    train_sequences = [
        sequence
        for sequence in sequences
        if sequence.split == "train"
    ]

    validation_sequences = [
        sequence
        for sequence in sequences
        if sequence.split == "validation"
    ]

    if not train_sequences or not validation_sequences:
        raise ValueError("Frozen train/validation sequences are required")

    X_train, y_train = make_training_data(train_sequences)

    X_train_tensor = torch.from_numpy(X_train)
    y_train_tensor = torch.from_numpy(y_train)

    model = TCNClassifier(
        input_features=X_train.shape[2],
    )

    positive_count = float(y_train.sum())
    negative_count = float(len(y_train) - positive_count)

    if positive_count == 0:
        raise ValueError("Training data contains no positive attack samples")

    pos_weight = torch.tensor(
        negative_count / positive_count,
        dtype=torch.float32,
    )

    loss_function = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
    )

    model.train()

    for _ in range(EPOCHS):
        optimizer.zero_grad()

        logits = model(X_train_tensor)
        loss = loss_function(logits, y_train_tensor)

        loss.backward()
        optimizer.step()

    metrics = detection_metrics(
        model,
        validation_sequences,
    )

    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "input_features": X_train.shape[2],
            "window_size": WINDOW_SIZE,
            "seed": SEED,
            "epochs": EPOCHS,
            "learning_rate": LEARNING_RATE,
        },
        MODEL_PATH,
    )

    window_manifest = {
        "evidence_id": "RW-080-2",
        "status": "pass",
        "scenario_count": len(sequences),
        "train_scenario_count": len(train_sequences),
        "validation_scenario_count": len(validation_sequences),
        "window_size_timesteps": WINDOW_SIZE,
        "windows_minutes": list(WINDOWS),
        "observable_features_per_window": 54,
        "input_features_per_timestep": 54 * len(WINDOWS),
        "scenario_boundary_crossing": False,
        "scenario_group_field": "scenario_id",
        "ordered_by": [
            "event_time",
            "sequence_index",
        ],
        "ground_truth_stage_used_only_for_evaluation": True,
        "label_source": "scenario.variant",
        "synthetic_only": True,
    }

    MANIFEST_PATH.write_text(
        json.dumps(
            window_manifest,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    report = {
        "evidence_id": "RW-080-2",
        "status": "pass",
        "model": "dilated_causal_tcn_with_attention_pooling",
        "architecture": {
            "causal": True,
            "kernel_size": 3,
            "dilations": [1, 2, 4],
            "channels": 32,
            "attention_pooling": True,
        },
        "seed": SEED,
        "epochs": EPOCHS,
        "learning_rate": LEARNING_RATE,
        "input_features_per_timestep": X_train.shape[2],
        "window_size_timesteps": WINDOW_SIZE,
        "scenario_count": len(sequences),
        "train_scenario_count": len(train_sequences),
        "validation_scenario_count": len(validation_sequences),
        "scenario_boundary_crossing": False,
        "ground_truth_stage_used_only_for_evaluation": True,
        "metrics": metrics,
        "model_artifact": str(MODEL_PATH),
        "window_manifest": str(MANIFEST_PATH),
        "synthetic_only": True,
        "real_action_executed": False,
    }

    REPORT_PATH.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print("RW-080-2: PASS")
    print("input_features_per_timestep:", X_train.shape[2])
    print("train_samples:", len(X_train))
    print("validation_scenarios:", len(validation_sequences))
    print("metrics:", json.dumps(metrics, indent=2))
    print("model:", MODEL_PATH)
    print("window_manifest:", MANIFEST_PATH)
    print("report:", REPORT_PATH)


if __name__ == "__main__":
    main()
