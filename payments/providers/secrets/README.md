# 🛠️ Tools

Helper scripts for exporting and importing credentials used by the `payments` automation tool.

## 🔐 Scripts

- `export_credentials.py` – Saves credentials from the system keyring to a local file (default: `.credentials`)
- `import_credentials.py` – Loads credentials from a local file and stores them in the system keyring

## ⚠️ Security Warning

Exported credentials are **not encrypted**.  
Use these scripts only in trusted environments and **never commit credential files to a public repository**.

## 📦 Example

```bash
python tools/export_credentials.py       # Export keyring → .credentials
python tools/import_credentials.py       # Import .credentials → keyring

# With explicit filenames:
python tools/export_credentials.py -o mycreds.env
python tools/import_credentials.py -i mycreds.env
```
