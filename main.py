import sys
import argparse

from commands.mirror_copy import mirror_copy
from commands.download import download_file
from config import load_config


def build_parser() -> argparse.ArgumentParser:

    config = load_config()

    parser = argparse.ArgumentParser(prog="comfyui-model-downloader",
                                     description="Download models files to a specific folder.")
    sub = parser.add_subparsers(dest="command",
                                required=True)

    download_config = config.get("download", {})
    p_dl = sub.add_parser("download",
                          help="Download a file to a folder")
    p_dl.add_argument("url",
                      help="URL of the file to download")
    p_dl.add_argument("--model-folder",
                      default=download_config.get("model_folder"),
                      help="the folder of the model or component")
    p_dl.add_argument("folder",
                      nargs='?',
                      default=None,
                      help="the folder of the model or component")

    mirror_copy_config = config.get("mirror-copy", {})
    p_cp = sub.add_parser("mirror-copy",
                          help="Mirror-copy models from source to destination with progress")
    p_cp.add_argument("source",
                      nargs='?',
                      default=mirror_copy_config.get("source"),
                      help="Source folder to mirror")
    p_cp.add_argument("destination",
                      nargs='?',
                      default=mirror_copy_config.get("destination"),
                      help="Destination folder to mirror into")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "download":
        try:
            path = download_file(args.url, args.model_folder, args.folder)
            print(f"Saved to: {path}")
            return 0
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    if args.command == "mirror-copy":
        try:
            mirror_copy(args.source, args.destination)
            print("Mirror copy completed.")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
