import hashlib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import sys


SUPPORTED_PYTHON = (3, 12)
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = REPOSITORY_ROOT / "requirements.lock"
LOCK_CHECKSUM_PATH = REPOSITORY_ROOT / "requirements.lock.sha256"


def read_locked_versions() -> dict[str, str]:
    locked: dict[str, str] = {}
    for raw_line in LOCK_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        package, expected_version = line.split("==", maxsplit=1)
        locked[package] = expected_version
    return locked


def verify_lock_checksum() -> str | None:
    expected = LOCK_CHECKSUM_PATH.read_text(encoding="utf-8").split()[0]
    actual = hashlib.sha256(LOCK_PATH.read_bytes()).hexdigest()
    if actual != expected:
        return f"requirements.lock checksum mismatch: expected {expected}, got {actual}"
    return None


def main() -> int:
    print("=== URAI Ransomware Resilience Environment Verification ===")
    print(f"Python: {sys.version.split()[0]}")

    failures: list[str] = []
    if sys.version_info[:2] != SUPPORTED_PYTHON:
        failures.append(
            "unsupported Python version: "
            f"expected {SUPPORTED_PYTHON[0]}.{SUPPORTED_PYTHON[1]}.x"
        )

    checksum_failure = verify_lock_checksum()
    if checksum_failure:
        failures.append(checksum_failure)

    for package, expected_version in read_locked_versions().items():
        try:
            installed_version = version(package)
        except PackageNotFoundError:
            failures.append(f"missing package: {package}=={expected_version}")
            continue

        print(f"{package}: {installed_version}")
        if installed_version != expected_version:
            failures.append(
                f"version mismatch for {package}: "
                f"expected {expected_version}, got {installed_version}"
            )

    if failures:
        print("Environment verification: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("requirements.lock SHA-256: PASS")
    print("Environment verification: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
