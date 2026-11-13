from enum import Enum
import re


class IdentifierType(str, Enum):
    ASSET = "asset"
    SITE = "site"
    SERVICE = "service"
    ACCOUNT = "account"
    DEPENDENCY = "dependency"


ID_PATTERNS = {
    IdentifierType.SITE: re.compile(
        r"^(energy|petrochemical)-[a-z0-9]+$"
    ),
    IdentifierType.ASSET: re.compile(
        r"^(energy|petrochemical)-[a-z0-9]+-asset-[a-z0-9-]+-\d{3}$"
    ),
    IdentifierType.SERVICE: re.compile(
        r"^(energy|petrochemical)-[a-z0-9]+-svc-[a-z0-9-]+$"
    ),
    IdentifierType.ACCOUNT: re.compile(
        r"^(energy|petrochemical)-[a-z0-9]+-acct-[a-z0-9-]+-\d{3}$"
    ),
    IdentifierType.DEPENDENCY: re.compile(
        r"^(energy|petrochemical)-[a-z0-9]+-dep-(?:protected-)?\d{3}$"
    ),
}


def is_valid_identifier(
    identifier: str,
    identifier_type: IdentifierType,
) -> bool:
    """Return True when an identifier follows the canonical format."""
    pattern = ID_PATTERNS[identifier_type]
    return bool(pattern.fullmatch(identifier))
