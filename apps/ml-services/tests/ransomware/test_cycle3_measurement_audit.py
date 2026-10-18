"""Tests for Cycle 3 measurement provenance auditing."""

from dataclasses import FrozenInstanceError, replace
from math import inf, nan

import pytest

from config.ransomware.scenarios.cycle3_measurement_audit import (
    VALUE_SOURCE_PRIORITY,
    Cycle3MeasurementAudit,
    audit_cycle3_measurements,
)
from config.ransomware.scenarios.cycle3_scenario_adapter import (
    build_cycle3_adapted_scenarios,
)
from config.ransomware.scenarios.scenario_event_assembler import (
    assemble_scenario_events,
)


@pytest.fixture(scope="module")
def sample_event():
    scenario = build_cycle3_adapted_scenarios().scenarios[0]
    return assemble_scenario_events(scenario)[0]


def make_event(sample_event, **attributes):
    return replace(sample_event, attributes=attributes)


def test_returns_audit_dataclass(sample_event):
    result = audit_cycle3_measurements([sample_event])
    assert isinstance(result, Cycle3MeasurementAudit)


def test_empty_input(sample_event):
    result = audit_cycle3_measurements([])
    assert result.event_count == 0
    assert result.measured_event_count == 0
    assert result.missing_event_count == 0
    assert result.nonfinite_value_count == 0
    assert result.source_counts == ()
    assert result.mixed_sources is False


def test_missing_value(sample_event):
    result = audit_cycle3_measurements([
        make_event(sample_event)
    ])
    assert result.missing_event_count == 1
    assert result.measured_event_count == 0
    assert result.source_counts == (("missing", 1),)


@pytest.mark.parametrize("source", VALUE_SOURCE_PRIORITY)
def test_each_numeric_source(sample_event, source):
    result = audit_cycle3_measurements([
        make_event(sample_event, **{source: 0.5})
    ])
    assert result.measured_event_count == 1
    assert result.source_counts == ((source, 1),)
    assert result.nonfinite_value_count == 0


def test_zero_is_valid_numeric_value(sample_event):
    result = audit_cycle3_measurements([
        make_event(sample_event, observable_value=0)
    ])
    assert result.measured_event_count == 1
    assert result.missing_event_count == 0


def test_boolean_is_not_numeric_measurement(sample_event):
    result = audit_cycle3_measurements([
        make_event(sample_event, observable_value=True)
    ])
    assert result.measured_event_count == 0
    assert result.missing_event_count == 1


def test_boolean_falls_through_to_next_source(sample_event):
    result = audit_cycle3_measurements([
        make_event(
            sample_event,
            observable_value=False,
            value=0.4,
        )
    ])
    assert result.source_counts == (("value", 1),)


def test_source_priority(sample_event):
    result = audit_cycle3_measurements([
        make_event(
            sample_event,
            observable_value=0.2,
            value=0.4,
            activity_intensity=0.6,
            degradation_severity=0.8,
        )
    ])
    assert result.source_counts == (("observable_value", 1),)


def test_mixed_sources_detected(sample_event):
    events = [
        make_event(sample_event, observable_value=0.2),
        make_event(sample_event, activity_intensity=0.6),
    ]
    result = audit_cycle3_measurements(events)
    assert result.mixed_sources is True
    assert result.measured_event_count == 2


def test_same_source_not_mixed(sample_event):
    events = [
        make_event(sample_event, value=0.2),
        make_event(sample_event, value=0.8),
    ]
    result = audit_cycle3_measurements(events)
    assert result.mixed_sources is False


def test_missing_plus_one_source_not_mixed(sample_event):
    events = [
        make_event(sample_event),
        make_event(sample_event, value=0.4),
    ]
    result = audit_cycle3_measurements(events)
    assert result.mixed_sources is False
    assert result.missing_event_count == 1


@pytest.mark.parametrize("invalid", [nan, inf, -inf])
def test_nonfinite_values_counted(sample_event, invalid):
    result = audit_cycle3_measurements([
        make_event(sample_event, observable_value=invalid)
    ])
    assert result.nonfinite_value_count == 1
    assert result.measured_event_count == 0
    assert result.missing_event_count == 0
    assert result.source_counts == (("observable_value", 1),)


def test_mixed_finite_nonfinite_and_missing(sample_event):
    events = [
        make_event(sample_event, value=0.5),
        make_event(sample_event, value=inf),
        make_event(sample_event),
    ]
    result = audit_cycle3_measurements(events)
    assert result.event_count == 3
    assert result.measured_event_count == 1
    assert result.nonfinite_value_count == 1
    assert result.missing_event_count == 1


def test_source_counts_sorted(sample_event):
    events = [
        make_event(sample_event, value=0.3),
        make_event(sample_event, activity_intensity=0.4),
        make_event(sample_event),
    ]
    result = audit_cycle3_measurements(events)
    assert result.source_counts == (
        ("activity_intensity", 1),
        ("missing", 1),
        ("value", 1),
    )


def test_accepts_generator(sample_event):
    events = (
        make_event(sample_event, value=0.3)
        for _ in range(3)
    )
    result = audit_cycle3_measurements(events)
    assert result.event_count == 3
    assert result.measured_event_count == 3


def test_deterministic(sample_event):
    events = [
        make_event(sample_event, value=0.3),
        make_event(sample_event),
    ]
    assert audit_cycle3_measurements(
        events
    ) == audit_cycle3_measurements(events)


def test_original_event_not_modified(sample_event):
    original = make_event(sample_event, value=0.7)
    original_attributes = dict(original.attributes)

    audit_cycle3_measurements([original])

    assert original.attributes == original_attributes


def test_audit_result_is_frozen(sample_event):
    result = audit_cycle3_measurements([
        make_event(sample_event, value=0.5)
    ])

    with pytest.raises(FrozenInstanceError):
        result.event_count = 999


def test_string_is_not_numeric(sample_event):
    result = audit_cycle3_measurements([
        make_event(sample_event, observable_value="0.5")
    ])
    assert result.missing_event_count == 1
    assert result.measured_event_count == 0
