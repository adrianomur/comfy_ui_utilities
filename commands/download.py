import os
import requests
import urllib.request
from tqdm import tqdm

MODELS_FOLDER = '/Volumes/shared/ComfyUI/models'

ALLOWED_FOLDERS = ['diffusion_models',
                   'vae',
                   'text_encoders',
                    'loras',
                    'controlnet',
                    'checkpoints',
                    'model_patches',
                    'clip_vision',
                    'upscale_models',
                    'audio_encoders',
                    'unet']

def download_file(url: str,
                  folder: str,
                  filename: str | None = None) -> str:

    if folder not in ALLOWED_FOLDERS:
        raise ValueError(f"Invalid type: {folder}. Available types: {ALLOWED_FOLDERS}")

    folder = os.path.join(MODELS_FOLDER, folder)
    os.makedirs(folder, exist_ok=True)
    if filename is None:
        filename = os.path.basename(urllib.request.urlparse(url).path) or "downloaded.file"

    dest_path = os.path.join(folder, filename)

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get("content-length", 0))
        block_size = 1024 * 1024  # 1MB chunks

        with open(dest_path, "wb") as f, tqdm(
                total=total_size, unit="B", unit_scale=True, desc=filename
        ) as progress:
            for chunk in r.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    progress.update(len(chunk))

    return dest_path
