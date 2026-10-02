from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from torch import nn

from config.ransomware.tcn_challenger import (
    WINDOW_SIZE,
    build_sequences,
    load_and_verify_scenarios,
    pad_sequence,
)

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "artifacts/ransomware/offline"
MODEL_PATH = REPORT_DIR / "rw0803_transformer_model.pt"
REPORT_PATH = REPORT_DIR / "rw0803_transformer_report.json"

SEED = 20260921
EPOCHS = 30
LEARNING_RATE = 0.001
DETECTION_THRESHOLD = 0.5


class CompactTransformer(nn.Module):
    def __init__(self, input_features: int):
        super().__init__()

        self.projection = nn.Linear(input_features, 32)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=32,
            nhead=4,
            dim_feedforward=64,
            dropout=0.1,
            batch_first=True,
            activation="gelu",
        )

        self.encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=2,
        )

        self.attention = nn.Linear(32, 1)
        self.classifier = nn.Linear(32, 1)

    def forward(self, x):
        x = self.projection(x)
        x = self.encoder(x)

        scores = self.attention(x).squeeze(-1)
        weights = torch.softmax(scores, dim=1)

        pooled = torch.sum(
            x * weights.unsqueeze(-1),
            dim=1,
        )

        return self.classifier(pooled).squeeze(-1)


def make_training_data(sequences):
    samples = []
    labels = []

    for sequence in sequences:
        for end in range(1, len(sequence.timesteps) + 1):
            samples.append(
                pad_sequence(sequence.timesteps[:end])
            )
            labels.append(
                1.0 if sequence.variant == "attack" else 0.0
            )

    return (
        np.asarray(samples, dtype=np.float32),
        np.asarray(labels, dtype=np.float32),
    )


def evaluate(model, sequences):
    model.eval()

    results = []
    attack_delays = []

    with torch.no_grad():
        for sequence in sequences:
            probabilities = []

            for end in range(1, len(sequence.timesteps) + 1):
                window = pad_sequence(
                    sequence.timesteps[:end]
                )

                probability = torch.sigmoid(
                    model(
                        torch.from_numpy(window).unsqueeze(0)
                    )
                ).item()

                probabilities.append(probability)

            detected_at = next(
                (
                    index
                    for index, probability in enumerate(probabilities)
                    if probability >= DETECTION_THRESHOLD
                ),
                None,
            )

            if sequence.variant == "attack" and detected_at is not None:
                attack_delays.append(detected_at)

            results.append(
                {
                    "scenario_id": sequence.scenario_id,
                    "variant": sequence.variant,
                    "detected": detected_at is not None,
                    "detected_at_timestep": detected_at,
                }
            )

    attacks = [
        result
        for result in results
        if result["variant"] == "attack"
    ]

    return {
        "attack_scenario_count": len(attacks),
        "detected_attack_count": sum(
            result["detected"] for result in attacks
        ),
        "attack_detection_rate": (
            sum(result["detected"] for result in attacks)
            / len(attacks)
            if attacks
            else 0.0
        ),
        "mean_detection_delay_timesteps": (
            float(np.mean(attack_delays))
            if attack_delays
            else None
        ),
        "false_positive_scenario_count": sum(
            result["detected"]
            for result in results
            if result["variant"] != "attack"
        ),
        "scenario_results": results,
    }


def main():
    torch.manual_seed(SEED)
    np.random.seed(SEED)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    _, frozen = load_and_verify_scenarios()
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

    X_train, y_train = make_training_data(train_sequences)

    model = CompactTransformer(
        input_features=X_train.shape[2],
    )

    positive_count = float(y_train.sum())
    negative_count = float(len(y_train) - positive_count)

    loss_function = nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor(
            negative_count / positive_count,
            dtype=torch.float32,
        )
    )

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
    )

    X_tensor = torch.from_numpy(X_train)
    y_tensor = torch.from_numpy(y_train)

    model.train()

    for _ in range(EPOCHS):
        optimizer.zero_grad()

        logits = model(X_tensor)
        loss = loss_function(logits, y_tensor)

        loss.backward()
        optimizer.step()

    metrics = evaluate(
        model,
        validation_sequences,
    )

    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "input_features": X_train.shape[2],
            "window_size": WINDOW_SIZE,
            "seed": SEED,
        },
        MODEL_PATH,
    )

    report = {
        "evidence_id": "RW-080-3",
        "status": "pass",
        "model": "compact_transformer_encoder",
        "architecture": {
            "encoder_layers": 2,
            "model_dimension": 32,
            "attention_heads": 4,
            "feedforward_dimension": 64,
            "attention_pooling": True,
        },
        "seed": SEED,
        "epochs": EPOCHS,
        "learning_rate": LEARNING_RATE,
        "input_features_per_timestep": X_train.shape[2],
        "window_size_timesteps": WINDOW_SIZE,
        "train_scenario_count": len(train_sequences),
        "validation_scenario_count": len(validation_sequences),
        "scenario_boundary_crossing": False,
        "ground_truth_used_only_for_labels_and_evaluation": True,
        "metrics": metrics,
        "model_artifact": str(MODEL_PATH),
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

    print("RW-080-3: PASS")
    print("input_features_per_timestep:", X_train.shape[2])
    print("train_samples:", len(X_train))
    print("metrics:", json.dumps(metrics, indent=2))
    print("model:", MODEL_PATH)
    print("report:", REPORT_PATH)


if __name__ == "__main__":
    main()
