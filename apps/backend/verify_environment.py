import sys

import fastapi
import httpx
import pydantic
import pytest


def main() -> None:
    print("=== URAI Ransomware Resilience Environment Verification ===")
    print(f"Python: {sys.version.split()[0]}")
    print(f"FastAPI: {fastapi.__version__}")
    print(f"Pydantic: {pydantic.__version__}")
    print(f"httpx: {httpx.__version__}")
    print(f"pytest: {pytest.__version__}")
    print("Environment verification: PASS")


if __name__ == "__main__":
    main()
