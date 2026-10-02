from config.ransomware.transformer_challenger import (
    CompactTransformer,
    load_and_verify_scenarios,
    build_sequences,
)


def test_transformer_sequences_match_tcn_contract():
    _, frozen = load_and_verify_scenarios()
    sequences = build_sequences(frozen)

    assert len(sequences) == 80

    for sequence in sequences:
        assert sequence.timesteps.ndim == 2
        assert sequence.timesteps.shape[1] == 162
        assert len(sequence.timesteps) == len(sequence.stages)
        assert sequence.scenario_id
        assert sequence.split


def test_compact_transformer_has_expected_architecture():
    model = CompactTransformer(162)

    assert model.projection.out_features == 32
    assert len(model.encoder.layers) == 2
    assert model.encoder.layers[0].self_attn.num_heads == 4
    assert model.classifier.out_features == 1
