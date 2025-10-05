import argparse
import os
import sys
import urllib.request
import requests
from tqdm import tqdm

confyui_model_folder = '/Volumes/shared/ComfyUI/models'

available_folders = ['diffusion_models',
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

    if folder not in available_folders:
        raise ValueError(f"Invalid type: {folder}. Available types: {available_folders}")

    folder = os.path.join(confyui_model_folder, folder)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="comfyui-model-downloader",
                                     description="Download models files to a specific folder.")
    sub = parser.add_subparsers(dest="command",
                                required=True)

    p_dl = sub.add_parser("download", help="Download a file to a folder")
    p_dl.add_argument("url", help="URL of the file to download")
    p_dl.add_argument("folder", help="the folder of the model or component")
    p_cp = sub.add_parser("mirror-copy", help="Mirror-copy models from source to destination with progress")
    p_cp.add_argument("source", help="Source folder to mirror")
    p_cp.add_argument("destination", help="Destination folder to mirror into")

    return parser

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "download":
        try:
            path = download_file(args.url, args.folder)
            print(f"Saved to: {path}")
            return 0
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    if args.command == "mirror-copy":
        try:
            # Lazy import to avoid importing when not needed
            from copy_models_folder import mirror as mirror_run
            mirror_run(args.source, args.destination)
            print("Mirror copy completed.")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    parser.print_help()
    return 2

if __name__ == "__main__":
    raise SystemExit(main())