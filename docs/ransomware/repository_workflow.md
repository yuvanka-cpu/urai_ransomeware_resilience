# Repository Workflow and Traceability

## Task unit

Every branch, commit, pull request, test group and review note must reference one RW task ID or a tightly related task group from the execution sheet.

Examples:

```text
branch: rw-0006-environment-verification
commit: RW-0006 verify locked runtime and dependency versions
pull request: RW-0006 — Stage 0 environment reproducibility
```

## Contract change order

Shared safety, provenance, schema and API contracts must be reviewed and merged before dependent implementation. Parallel work must not make conflicting edits to the same controlled contract.

## Required review evidence

Each submission must identify:

- repository URL;
- exact commit hash;
- included RW task IDs;
- commands used for environment and test verification;
- links or paths to generated evidence;
- known warnings, failures or limitations.

Source-code ZIP files are supplemental review packages and do not replace Git history. The repository owner must provide the remote URL and reviewed commit hash before RW-0007 can be marked Done.
