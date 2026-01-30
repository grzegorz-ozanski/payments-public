# 💰 Payments Collector

![CI Linux](https://github.com/grzegorz-ozanski/payments/actions/workflows/run-linux.yml/badge.svg)
![CI Windows](https://github.com/grzegorz-ozanski/payments/actions/workflows/run-windows.yml/badge.svg)
[![Unit tests](https://github.com/grzegorz-ozanski/payments-public/actions/workflows/tests.yml/badge.svg)](https://github.com/grzegorz-ozanski/payments-public/actions/workflows/tests.yml)
![Coverage](https://img.shields.io/badge/coverage-62%25-yellow)  
Automation tool for retrieving outstanding payment information from various utility providers' online portals.

## ✨ Features

- ✅ Modular provider system (Energa, PGNiG, Multimedia, etc.)
- ✅ Selenium automation with headless Chrome
- ✅ Centralized logging and error handling
- ✅ Fallback mechanism for failed or unavailable providers
- ✅ Formatted output to console or file

## 📋 Requirements

- Python 3.10+
- pip

## 📦 Installation

```bash
git clone https://github.com/grzegorz-ozanski/payments-public.git
cd payments
git clone https://github.com/grzegorz-ozanski/browser.git
# Create Python virtual environment (recommended)
python -m venv .venv
# Activate .venv for your platform, e.g.:
#   source .venv/bin/activate      (Linux/macOS)
#   .venv\Scripts\activate.bat     (Windows cmd)
#   .venv\Scripts\Activate.ps1     (Windows PowerShell)
python -m pip install --upgrade pip
pip install -r requirements.txt  # includes browser dependencies
# Optional, for development purposes
cp hooks/* .git/hooks/
chmod +x .git/hooks/pre-push .git/hooks/pre-commit
```

## ⚙️ Configuration

You can configure logging and browser behavior via environment variables.  
See README.md of the browser library for full details.

## 🔐 Credentials

Each provider requires its own credentials. These can be read from the **system keyring** (recommended) or from **environment variables** (not secure, use only for development).

### 🔑 Keyring (preferred)

For each service, define a pair of credentials (`username`, `password`) under the same service name:

```python
import keyring

keyring.set_password(service_name='service_name', username='username', password='your_username')
keyring.set_password(service_name='service_name', username='password', password='your_password')

# To retrieve:
keyring.get_password('service_name', 'username')
keyring.get_password('service_name', 'password')
```

### ⚠️ Environment variables (not secure)

For each service `SERVICE_NAME`, define the following variables:

```bash
SERVICE_NAME_USERNAME='your_username'
SERVICE_NAME_PASSWORD='your_password'
```

### 🛠 Credential management helpers

You can use the helper scripts from the `tools/` directory to import/export credentials between a `.credentials` file and the system keyring:

```bash
python tools/export_credentials.py
python tools/import_credentials.py
```

## 🚀 Usage

### Basic usage:

```bash
python main.py
```

### Command-line arguments:
| Short          | Long                         | Meaning                                                                                                                                                                                      |
|----------------|------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| -c             | --clear-profile-on-exit      | Clear browser user profile on exit                                                                                                                                                           |
| -l false/true  | --headless false/true        | Toggle headless browser mode (default: auto)                                                                                                                                                 |
| -d debug_flags | --debug debug_flags          | Comma-separated list of debug flags<ul><li>bp: browser profile creation debugging</li><li>ml: Multimedia provider login debugging</li></ul>Using this option implicitly enables verbose mode |
| -o file_name   | --output OUTPUT              | Write retrieved payments to output file (UTF-8)                                                                                                                                              |
| -p name        | --provider name              | Run for single provider only (name must match one from the list below)                                                                                                                       |
| -t             | --trace                      | Enable trace logging for browser actions                                                                                                                                                     |
| -v             | --verbose                    | Enable verbose mode (show debug logs)                                                                                                                                                        |
|                | --persistent-profile-dir dir | Persisten browser profile directory location (default: user temp directory)                                                                                                                  |
|                | --chrome-path CHROME_PATH    | Use provided Chrome binary instead of automatically downloading                                                                                                                              |

Available providers: Provider, Actum, Energa, Multimedia, Nordhome, Opec, Opec2, Pgnig, Pewik, Vectra

### Environment variables
Program behavior can be modified using the following environment variables"

| Variable name                   | Default                                        | Values                                 | Meaning                                                                                  | Remarks                                              |
|---------------------------------|------------------------------------------------|----------------------------------------|------------------------------------------------------------------------------------------|------------------------------------------------------|
| BROWSER_LOG_LEVEL               | DEBUG                                          | Any valid Python log level or TRACE    | Logging level                                                                            |                                                      |
| BROWSER_LOG_FORMATTING          | %(levelname)s:%(name)s %(asctime)s %(message)s | Any valid Python log formatting string | Logging format string                                                                    |                                                      |
| BROWSER_LOG_TO_CONSOLE          | True                                           | True/False                             | If logs should be written to console or only to a file provided in  BROWSER_LOG_FILENAME |                                                      |
| BROWSER_LOG_FILENAME            | <empty>                                        | Valid file name                        | Name of the log file                                                                     |                                                      |
| BROWSER_DEBUG_PROFILE           | 0                                              | 0/1                                    | Debug browser profile creation                                                           | Set automatically with "-d bp" command line argument |
| PAYMENTS_DEBUG_MULTIMEDIA_LOGIN | 0                                              | 0/1                                    | Debug Multimedia provider login process                                                  | Set automatically with "-d ml" command line argument |
### Examples:

```bash
python main.py                         # Print payment data to console
python main.py -o output.txt           # Also write output to a file
```

## 📊 Example Output

```
pgnig   12,34  Dom   02-06-2025
energa  567,86 Biuro 26-05-2025
```

## 🧪 Testing

### ✅ Unit Testing

The codebase achieves **58% total test coverage**, focused on core logic:

- ✅ Business logic modules (`payments`, `lookuplist`) are tested above 90%
- ✅ Application entrypoint (`main.py`) is tested with mocks
- ⚠️ Web provider integrations (`providers/*`) are not tested in depth, as they require real Selenium sessions and are better suited for functional testing

We prioritize tests that cover:
- data parsing and validation
- sorting, grouping, formatting
- fallback logic and error handling

To check coverage locally:

```bash
pip install -r requirements-dev.txt
pytest --cov=payments --cov=providers --cov=lookuplist --cov-report=term --cov-report=html
```

📂 Detailed HTML report: `htmlcov/index.html`

### ✅ Static analysis
Codebase is compliant with static code checking with both PyCharm and mypy tools.
All exceptions are explicitly documented.

#### mypy
To run mypy check, use:
```bash
pip install types-requests types-python-dateutil
mypy . --strict --ignore-missing-imports --exclude run
```
#### ruff
To run ruff check, use:
```bash
ruff check .
```
#### pyright

To use Pyright:
1. Install Node.js - https://nodejs.org/
2. Install pyright globally:
   * Linux/macOS:
   ```bash
   npm install -g pyright
   ```
   * Windows (cmd/PowerShell):
   ```bash
   npm install -g pyright
   ```
3. Run from the project root:
```bash
pyright
```
Documentation: https://github.com/microsoft/pyright

### 🤖 Continuous Integration (CI)

This project includes CI workflows for both **Linux** and **Windows**, powered by GitHub Actions.

CI covers:

- Automated Selenium test runs
- Output verification via reference snapshots
- Status tracking (e.g., FAILED → PASSED transitions)
- Secret masking in logs via PowerShell filters

> See [README_actions.md](.github/README_actions.md) for full workflow logic.  
> Reference output used in CI is downloaded from a private repo to avoid exposing sensitive data. Any change to output must be explicitly reviewed and committed.  
> For security reasons, CI tests are run only in private repo copy

### 🏃 Dynamic runner selection in reusable workflows

CI schedulers for Linux and Windows use a shared reusable workflow defined in `run-tests.yml`.  
The runner is passed via the `runner-label` input, allowing flexible execution on different platforms.

Due to GitHub Actions limitations, this input must be a **JSON-formatted string array**, which is then converted to a real list using `fromJson()`:

✅ **Correct usage:**
```
with:
  runner-label: '["self-hosted", "Linux"]'
```

❌ **Invalid:**
```
with:
  runner-label: self-hosted, Linux
```

In the reusable workflow:
```
runs-on: ${{ fromJson(inputs.runner-label) }}
```

This allows you to use multi-label runners like:
- `["self-hosted", "Linux"]`
- `["self-hosted", "Windows"]`

Make sure your self-hosted runners are registered with appropriate labels.

## 🗂️ Project Structure

```
payments/
├── browser/        # Reusable Chrome automation components
├── lookuplist/     # Fallback-capable key-value store
├── payments/       # Payment model and manager logic
├── providers/      # Provider-specific logic (e.g. login, scraping)
├── tools/          # Scripts for credential import/export
├── main.py         # Entrypoint
└── README.md       # This file
```

## 🙋 Author

Created with ❤️ by [**Grzegorz Ożański**](https://github.com/grzegorz-ozanski)  

with a little help from [ChatGPT](https://chat.openai.com/) — for structure, suggestions and sleepless debugging sessions 😉

This project is part of my public portfolio — feel free to explore, learn from it, or reach out.

## 📄 License

MIT License
