import sys
import argparse

from commands.mirror_copy import mirror_copy
from commands.mirror_copy_remote import mirror_copy_remote
from commands.download import download_file
from commands.restore_settings import run as restore_settings
from commands.remove_unused_models import remove_unused_models
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
    p_dl.add_argument("--urls",
                      nargs='+',
                      required=True,
                      help="URLs of the files to download")
    p_dl.add_argument("--model-folder",
                      default=download_config.get("model_folder"),
                      help="the folder of the model or component")
    p_dl.add_argument("--folder",
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

    mirror_copy_remote_config = config.get("mirror-copy-remote", {})
    p_cp_remote = sub.add_parser("mirror-copy-remote",
                                 help="Mirror-copy models from source to remote destination using rsync")
    p_cp_remote.add_argument("source",
                             nargs='?',
                             default=mirror_copy_remote_config.get("source"),
                             help="Source folder to mirror")
    p_cp_remote.add_argument("destination",
                             nargs='?',
                             default=mirror_copy_remote_config.get(
                                 "destination"),
                             help="Destination folder (local or remote in format user@host:/path)")

    sub.add_parser("restore-settings",
                   help="Restore ComfyUI settings")
    p_remove = sub.add_parser("remove-unused",
                              help="Remove unused models based on last access time")
    p_remove.add_argument("--folder",
                          default=r"C:/Users/adriano/Desktop/models",
                          help="Folder to scan for unused models")
    p_remove.add_argument("--days",
                          type=int,
                          default=15,
                          help="Minimum number of days since last access")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "download":
        try:
            for url in args.urls:
                path = download_file(url, args.model_folder, args.folder)
                print(f"Saved {url} to: {path}")
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

    if args.command == "mirror-copy-remote":
        try:
            mirror_copy_remote(args.source, args.destination)
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    if args.command == "restore-settings":
        try:
            restore_settings()
            print("Settings restored successfully.")
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    if args.command == "remove-unused":
        try:
            remove_unused_models(args.folder, args.days)
            return 0
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
