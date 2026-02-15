# ComfyUI Utilities

CLI utilities for managing [ComfyUI](https://github.com/comfyanonymous/ComfyUI) models, settings, and workflows. Download models, mirror folders, restore a portable ComfyUI setup, and clean up unused model files.

## Requirements

- Python 3.13+
- Optional: [uv](https://github.com/astral-sh/uv) for install and run

## Installation

From the project root:

```bash
# With uv
uv sync
uv run python main.py --help

# Or with pip
pip install -e .
python main.py --help
```

## Configuration

Create a `config.json` in the project root (or pass paths via CLI options). Example structure:

```json
{
  "general": {
    "comfyui_folder": "C:\\path\\to\\ComfyUI_windows_portable",
    "models_folder": "C:\\path\\to\\models",
    "outputs_directory": "C:\\path\\to\\outputs"
  },
  "mirror-copy": {
    "source": "Z:\\ComfyUI\\models"
  },
  "download": {
    "remote_models_folder": "/path/to/ComfyUI/models"
  },
  "restore-settings": {
    "shortcut_path": "C:\\path\\to\\ComfyUI",
    "repositories": [
      "https://github.com/Comfy-Org/ComfyUI-Manager.git",
      "https://github.com/your/custom-node.git"
    ]
  }
}
```

Paths in `config.json` are used as defaults when you don’t pass arguments or options.

## Commands

### `download`

Download model files from URLs into your models tree. Supports standard ComfyUI subfolders (e.g. `checkpoints`, `loras`, `vae`, `controlnet`). Skips files that already exist with the same size.

```bash
# One URL (folder inferred from URL path)
uv run python main.py download --urls "https://example.com/models/checkpoints/model.safetensors"

# Multiple URLs and optional overrides
uv run python main.py download --urls "https://..." --urls "https://..." --model-folder /path/to/models --folder loras
```

**Options:**

- `--urls` — One or more URLs to download (repeat for multiple).
- `--model-folder` — Base models directory (default from `config.download.remote_models_folder`).
- `--folder` — Override subfolder (e.g. `loras`, `checkpoints`); if omitted, derived from the URL path.

Allowed folder names: `diffusion_models`, `vae`, `text_encoders`, `loras`, `controlnet`, `checkpoints`, `model_patches`, `clip_vision`, `upscale_models`, `audio_encoders`, `unet`, `latent_upscale_models`.

---

### `mirror-copy`

Mirror a source folder to a destination: same directory layout, skip files that already match (size + mtime), remove files in the destination that don’t exist in the source. Progress is shown in bytes.

```bash
uv run python main.py mirror-copy [SOURCE] [DESTINATION]
```

If `SOURCE` or `DESTINATION` are omitted, they are taken from `config.mirror-copy.source` and `config.general.models_folder` respectively.

---

### `restore-settings`

Set up a portable ComfyUI install from your config:

- Creates `run_nvidia_gpu_custom.bat` with your custom output directory.
- Creates a symlink from that batch file to `restore-settings.shortcut_path`.
- Clones or updates custom node repos listed in `restore-settings.repositories` into `ComfyUI/custom_nodes` and installs their `requirements.txt`.
- Creates a symlink from `general.models_folder` to `ComfyUI/models`.

```bash
uv run python main.py restore-settings
```

Uses `config.general` and `config.restore-settings` only; no extra CLI options.

---

### `remove-unused`

Delete files under a folder that haven’t been accessed in at least `N` days, and write the list of removed paths to `removed_models.json` in that folder.

```bash
uv run python main.py remove-unused --folder "C:\path\to\models" --days 15
```

**Options:**

- `--folder` — Directory to scan (default in code is a Windows path; override for your setup).
- `--days` — Minimum days since last access (default: 15).

**Warning:** This permanently deletes files. Ensure `--folder` and `--days` are correct before running.

## Project layout

```
comfy_ui_utilities/
├── main.py           # CLI entry (click)
├── config.py         # Config loading
├── config.json       # Your config (create from example above)
├── pyproject.toml
└── commands/
    ├── download.py
    ├── mirror_copy.py
    ├── mirror_copy_remote.py   # Used for remote rsync over SSH (not in CLI)
    ├── restore_settings.py
    └── remove_unused_models.py
```
