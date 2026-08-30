# Known Verification Warnings

## Starlette TestClient deprecation

The Stage 0 test run passes but emits one upstream `StarletteDeprecationWarning`: the bundled `fastapi.testclient` compatibility layer currently imports the deprecated `httpx`-based Starlette test client and recommends `httpx2`.

The warning is not suppressed. Runtime dependencies remain exactly pinned for reproducibility, and migration of the test transport must be handled as an explicit dependency-update task with contract tests. It does not affect the 37 passing Stage 0 assertions.
