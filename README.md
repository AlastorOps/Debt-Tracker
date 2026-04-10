# Debt Tracker

A desktop application for tracking personal debts, built with Python and Tkinter.

---

## Features

- Add, edit, and delete debt records
- Track **name**, **phone number**, **amount**, **interest rate**, **date**, and **notes** per record
- Automatic **total calculation** with interest applied
- Mark records as **Paid** or **Unpaid**
- **Search** across name, phone, notes, and status
- **Filter** by All / Paid / Unpaid
- **Sort** by any column — click a column header to sort, click again to reverse
- **Total Unpaid** summary (includes interest) shown at a glance
- **Light and Dark mode**
- Date picker or manual date entry with auto-format detection
- Data stored locally in a SQLite database — nothing leaves your machine

---

## Requirements

- Python 3.8+
- [tkcalendar](https://pypi.org/project/tkcalendar/)

Install dependencies:

```bash
pip install tkcalendar
```

---

## Running from Source

```bash
python debt_tracker.py
```

---

## Building the Executable

Requires [PyInstaller](https://pyinstaller.org):

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=debt_tracker_icon.ico --name="DebtTracker" debt_tracker.py
```

The compiled executable will be at `dist/DebtTracker.exe`.

---

## Building the Installer

Requires [NSIS](https://nsis.sourceforge.io). After building the exe:

1. Build the exe (see above) so `dist/DebtTracker.exe` exists
2. Right-click `installer.nsi` → **Compile NSIS Script**
3. This produces `DebtTracker_Setup.exe`

The installer:
- Installs to `C:\Program Files\DebtTracker`
- Creates a Desktop shortcut
- Adds a Start Menu entry
- Registers with Windows **Add or Remove Programs**

---

## Data Storage

Your database is saved at:

```
Documents\DebtTracker\debt_tracker.db
```

Uninstalling the app does **not** delete this file — your data is always preserved.

---

## Project Structure

```
DebtTracker/
├── debt_tracker.py        # Main application
├── debt_tracker_icon.ico  # App icon
├── installer.nsi          # NSIS installer script
└── README.md
```

---

## License

Personal use. Built by Alastor.
