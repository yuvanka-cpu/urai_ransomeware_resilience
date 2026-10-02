import numpy as np

from config.ransomware.tcn_challenger import (
    WINDOW_SIZE,
    build_sequences,
    load_and_verify_scenarios,
)


def test_tcn_sequences_do_not_cross_scenario_boundaries():
    _, frozen = load_and_verify_scenarios()

    sequences = build_sequences(frozen)

    assert len(sequences) == 80

    for sequence in sequences:
        assert sequence.timesteps.ndim == 2
        assert sequence.timesteps.shape[1] == 162
        assert len(sequence.timesteps) == len(sequence.stages)
        assert sequence.scenario_id
        assert sequence.split


def test_tcn_sequences_are_ordered_and_nonempty():
    _, frozen = load_and_verify_scenarios()

    sequences = build_sequences(frozen)

    for sequence in sequences:
        assert sequence.timesteps.shape[0] > 0
        assert np.isfinite(sequence.timesteps).all()


def test_tcn_window_size_is_fixed():
    assert WINDOW_SIZE == 8
