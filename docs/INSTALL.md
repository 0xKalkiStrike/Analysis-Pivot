# Installation Guide

## Prerequisites

- **Python 3.10 or newer** (3.11 or 3.13 recommended).
- **pip 23+**.
- On Linux you may need OS-level Qt runtime libraries:
  ```bash
  sudo apt-get install -y libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 libxcb-image0 \
                          libxcb-keysyms1 libxcb-render-util0 libxcb-shape0 libgl1
  ```

## Steps

1. **Clone / download** the project.
2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate       # Windows: .venv\Scripts\activate
   ```
3. **Install requirements**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **Generate demo data** (optional):
   ```bash
   python scripts/generate_samples.py samples
   ```
5. **Run the desktop app**:
   ```bash
   python run.py
   ```

## Troubleshooting

- **Qt "platform plugin" errors on Linux**: install the packages listed above.
- **`ImportError: pyarrow is required`**: `pip install pyarrow`.
- **Excel `.xlsb` files fail to load**: install `pyxlsb` (already in requirements).
- **Large files feel slow to load initially**: consider using CSV or `--limit` in CLI while previewing.

## Building a Distributable Binary

```bash
python scripts/build.py --onefile
```

The executable is emitted to `dist/ExcelIntel/`.

## Data locations

The app stores its config and projects in the user profile:

- Config      : `~/.excelintel/config.json`
- Projects    : `~/.excelintel/projects/*.eip`
- Logs        : `~/.excelintel/logs/excelintel.log`
- Cache       : `~/.excelintel/cache/`
- Exports     : `~/.excelintel/exports/`

Delete the folder to reset the app.
