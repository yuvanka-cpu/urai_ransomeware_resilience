from dataclasses import dataclass


@dataclass(frozen=True)
class UseCaseFamily:
    use_case_id: str
    industry: str
    description: str


ENERGY_USE_CASES = (
    UseCaseFamily(
        "energy_generation_support",
        "energy",
        "Generation support systems",
    ),
    UseCaseFamily(
        "energy_substation_support",
        "energy",
        "Substation support",
    ),
    UseCaseFamily(
        "energy_transmission_distribution_support",
        "energy",
        "Transmission and distribution support",
    ),
    UseCaseFamily(
        "energy_control_centre_support",
        "energy",
        "Control centre support",
    ),
    UseCaseFamily(
        "energy_engineering_historian_support",
        "energy",
        "Engineering workstation and historian support",
    ),
)


PETROCHEMICAL_USE_CASES = (
    UseCaseFamily(
        "petrochemical_refinery_it_support",
        "petrochemical",
        "Refinery enterprise IT support",
    ),
    UseCaseFamily(
        "petrochemical_dcs_support",
        "petrochemical",
        "DCS and SCADA support",
    ),
    UseCaseFamily(
        "petrochemical_engineering_historian_support",
        "petrochemical",
        "Engineering workstation and historian support",
    ),
    UseCaseFamily(
        "petrochemical_batch_quality_support",
        "petrochemical",
        "Batch and quality support",
    ),
    UseCaseFamily(
        "petrochemical_terminal_loading_support",
        "petrochemical",
        "Terminal and loading support",
    ),
)


ALL_USE_CASES = ENERGY_USE_CASES + PETROCHEMICAL_USE_CASES

SCENARIO_VARIANTS = (
    "normal",
    "attack",
    "benign",
    "fault",
)
