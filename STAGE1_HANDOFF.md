# Stage 1 Handoff

This package starts from the independently verified Stage 0 commit `fe9a3f98d78cdf30485445cf93b9fac49789d5fd`. It contains proposed Stage 1 contracts for RW-0101 through RW-0107. They are ready for Yuvanka's review, not yet marked Done.

## Apply safely

1. Make sure the current repository has no uncommitted work that could be overwritten.
2. Update `main` and create a Stage 1 branch:

```bash
git checkout main
git pull origin main
git checkout -b rw-0101-stage1-contracts
```

3. Copy the contents of the package's `urai_ransomeware_resilience-main` folder into the local repository root. Do not replace or delete the local `.git` directory.
4. Review the ten use cases, safety language and acceptance thresholds against the task sheet and FINAL v3 blueprint.
5. From `apps/backend`, run:

```bash
../../.venv/Scripts/python.exe verify_environment.py
../../.venv/Scripts/python.exe -m pytest -q
```

6. Review the changed-file list before committing:

```bash
git status --short
git diff --check
git diff
```

7. Stage only the reviewed Stage 1 files, commit and push:

```bash
git add README.md STAGE1_HANDOFF.md apps/backend/app apps/backend/tests apps/ml-services/config/ransomware docs/ransomware
git commit -m "RW-0101-RW-0107 define Stage 1 ransomware contracts"
git push -u origin rw-0101-stage1-contracts
```

Send back the repository URL, exact commit hash, test output and any wording Yuvanka changed. Stage 1 can be marked Done only after that commit is independently checked. Dataset generation remains Stage 4.
