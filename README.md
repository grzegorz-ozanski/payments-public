# 💰 Payments Collector

Automation tool for retrieving outstanding payment information from various utility providers' online portals.

## ✨ Features

- ✅ Modular provider system (Energa, PGNiG, Multimedia, etc.)
- ✅ Selenium automation with headless Chrome
- ✅ Centralized logging and error handling
- ✅ Fallback mechanism for failed or unavailable providers
- ✅ Formatted output to console or file

## 📋 Requirements

- Python 3.10+
- Google Chrome (ChromeDriver will be auto-downloaded)
- pip

## 📦 Installation

```bash
git clone https://github.com/grzegorz-ozanski/payments.git
cd payments
git clone https://github.com/grzegorz-ozanski/browser.git
pip install -r requirements.txt  # includes browser dependencies
```

## ⚙️ Configuration

You can configure logging behavior via environment variables.  
See [`browser/README.md`](browser/README.md) for full details.

## 🔐 Credentials

Each provider requires its own credentials. These can be read from the **system keyring** (recommended) or from **environment variables** (unsafe, use only for development).

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

You can use the helper scripts from the `tools/` directory to import/export credentials between `.credentials` file and system keyring:

```bash
python tools/export_credentials.py
python tools/import_credentials.py
```

## 🚀 Usage

Basic usage:

```bash
python main.py
```

Examples:

```bash
python main.py                         # Print payment data to console
python main.py -o output.txt           # Also write output to a file
```

## 🧪 Testing

### CI
This project includes CI workflows for both **Linux** and **Windows**, powered by GitHub Actions.

The CI logic covers:

- Automated test runs with Selenium
- Output verification via reference snapshots
- Status tracking (detecting changes like FAILED → PASSED)
- Secret masking in logs via custom PowerShell scripts

> See [.github/](.github/) for full CI configuration details.

### Unittesting
🟡 *TODO — test suite coming soon*

## 🗂️ Project Structure

```text
payments/
├── browser/        # Reusable Chrome automation components
├── lookuplist/     # Fallback-capable key-value store
├── payments/       # Payment model, manager logic
├── providers/      # Provider-specific logic (e.g. login, scraping)
├── tools/          # Scripts for credential import/export
├── main.py         # Entry point
└── README.md       # This file
```

## 🙋 Author

Created with ❤️ by [**Grzegorz Ożański**](https://github.com/grzegorz-ozanski)  
with a little help from [ChatGPT](https://chat.openai.com/) — for structure, suggestions & sleepless debugging sessions 😉

This project is part of my public portfolio — feel free to explore, learn from it, or reach out.

## 📄 License

MIT License
