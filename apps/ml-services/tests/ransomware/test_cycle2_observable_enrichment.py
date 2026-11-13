from config.ransomware.features.cycle2_observable_enrichment import (
    enrich_cycle2_events,
)
from config.ransomware.scenarios.scenario_event_assembler import (
    ObservableScenarioEvent,
)


def make_event(event_type, event_family, attributes=None):
    return ObservableScenarioEvent(
        scenario_id="test-scenario-001",
        scenario_seed=20260921,
        split="train",
        sequence_index=1,
        event_time="2026-01-01T00:00:00Z",
        event_family=event_family,
        event_type=event_type,
        asset_id="test-asset-001",
        attributes=attributes or {},
    )


def test_enrichment_is_deterministic():
    event = make_event(
        "encryption_impact_observable",
        "file",
    )

    first = enrich_cycle2_events([event])
    second = enrich_cycle2_events([event])

    assert first == second


def test_existing_attributes_are_preserved_without_mutation():
    original_attributes = {
        "source_host": "known-host",
        "custom_evidence": 42,
    }
    event = make_event(
        "authentication_fan_out",
        "authentication",
        original_attributes,
    )

    enriched = enrich_cycle2_events([event])

    assert enriched[0].attributes["source_host"] == "known-host"
    assert enriched[0].attributes["custom_evidence"] == 42
    assert original_attributes == {
        "source_host": "known-host",
        "custom_evidence": 42,
    }


def test_zone_crossing_does_not_fabricate_stage_transition():
    event = make_event(
        "zone_crossings",
        "network",
    )

    enriched = enrich_cycle2_events([event])

    assert enriched[0].attributes["zone_crossing"] is True
    assert "stage_transition_score" not in enriched[0].attributes
