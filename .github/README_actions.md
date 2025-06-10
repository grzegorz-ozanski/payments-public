# ⚙️ GitHub Actions – CI Workflows & Utilities

This folder contains CI/CD configuration and custom scripts used to verify the correctness and reliability of the automation logic.

## 🧪 Workflows

- `workflows/run-linux.yml` — Main CI pipeline for Linux
- `workflows/run-windows.yml` — Main CI pipeline for Windows

Both verify cross-platform compatibility and ensure headless browser automation works reliably on different OSes.

## 🛠️ Scripts

Located in `scripts/`, these PowerShell scripts are used in the CI process:

- `compare-output.ps1` — Compares test output with reference data
- `compare-status.ps1` — Detects if job status has changed (e.g., FAILED → PASSED)
- `mask-env-secrets.ps1` — Hides sensitive data from logs

## 🔐 Reference Data

To avoid publishing sensitive payment amounts, reference test output is stored in a **private repository** and downloaded during CI using a GitHub token (`TESTDATA_PAT` secret).  
This token must grant `read` access to the private testdata repository.

Temporary files such as `test_output.txt` are created during workflow runs and compared against the reference snapshot.

## 📍 Status Tracking

- `status/last-status.txt` — Stores the result of the last run for status-change detection
