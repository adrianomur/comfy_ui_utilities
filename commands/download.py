import os
import requests
import urllib.request
from tqdm import tqdm

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
                   'unet',
                   'model_patches',
                   'latent_upscale_models']


def download_file(url: str,
                  model_folder: str,
                  folder: str | None = None,
                  filename: str | None = None) -> str:

    if not folder:
        url_parts = urllib.request.urlparse(url).path.split('/')
        folder = url_parts[-2]
    
    if folder not in ALLOWED_FOLDERS:
        raise ValueError(
            f"Invalid type: {folder}. Available types: {ALLOWED_FOLDERS}")

    folder = os.path.join(model_folder, folder)
    os.makedirs(folder, exist_ok=True)
    if filename is None:
        filename = os.path.basename(
            urllib.request.urlparse(url).path) or "downloaded.file"

    dest_path = os.path.join(folder, filename)

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get("content-length", 0))
        # If the destination file already exists and sizes match, skip download
        if total_size > 0 and os.path.exists(dest_path) and os.path.getsize(dest_path) == total_size:
            return dest_path
        block_size = 1024 * 1024  # 1MB chunks

        temp_path = os.path.join(folder, f"_incomplete_{filename}")

        with open(temp_path, "wb") as f, tqdm(
                total=total_size, unit="B", unit_scale=True, desc=filename
        ) as progress:
            for chunk in r.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    progress.update(len(chunk))

    # Move the completed temp file into place atomically
    if os.path.exists(temp_path):
        os.replace(temp_path, dest_path)

    return dest_path
