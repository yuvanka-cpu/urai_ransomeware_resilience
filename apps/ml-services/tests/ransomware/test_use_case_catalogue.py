from config.ransomware.scenarios.use_case_catalogue import (
    ALL_USE_CASES,
    ENERGY_USE_CASES,
    PETROCHEMICAL_USE_CASES,
    SCENARIO_VARIANTS,
)


def test_contains_five_energy_use_cases():
    assert len(ENERGY_USE_CASES) == 5
    assert all(use_case.industry == "energy" for use_case in ENERGY_USE_CASES)


def test_contains_five_petrochemical_use_cases():
    assert len(PETROCHEMICAL_USE_CASES) == 5
    assert all(
        use_case.industry == "petrochemical"
        for use_case in PETROCHEMICAL_USE_CASES
    )


def test_contains_ten_total_use_cases():
    assert len(ALL_USE_CASES) == 10
    assert len({use_case.use_case_id for use_case in ALL_USE_CASES}) == 10


def test_each_use_case_requires_four_variants():
    assert set(SCENARIO_VARIANTS) == {
        "normal",
        "attack",
        "benign",
        "fault",
    }
