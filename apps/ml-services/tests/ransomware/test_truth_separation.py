from pathlib import Path


BASE = Path("data/synthetic/ransomware_poc")
TRUTH = BASE / "truth"
OBSERVABLES = BASE / "observables"


def test_observable_and_truth_directories_are_separate():
    assert OBSERVABLES.exists()
    assert TRUTH.exists()
    assert OBSERVABLES != TRUTH


def test_all_required_truth_categories_exist():
    categories = (
        "scenario",
        "affected_assets",
        "blast_radius",
        "stage",
        "recovery_order",
    )

    for category in categories:
        assert (TRUTH / category).exists()


def test_truth_is_not_nested_inside_observables():
    assert not (OBSERVABLES / "truth").exists()


def test_truth_categories_are_physically_separate():
    paths = [
        TRUTH / "scenario",
        TRUTH / "affected_assets",
        TRUTH / "blast_radius",
        TRUTH / "stage",
        TRUTH / "recovery_order",
    ]

    assert len({path.resolve() for path in paths}) == 5
