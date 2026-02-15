import sys
import click

from commands.mirror_copy import mirror_copy
from commands.mirror_copy_remote import mirror_copy_remote
from commands.download import download_file
from commands.restore_settings import run as restore_settings
from commands.remove_unused_models import remove_unused_models
from config import load_config


def _get_config():
    return load_config()


@click.group(
    name="comfyui-model-downloader",
    invoke_without_command=True,
    no_args_is_help=True,
)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Download model files to a specific folder and other ComfyUI utilities."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = _get_config()


@cli.command("download", help="Download a file to a folder")
@click.option(
    "--urls",
    required=True,
    multiple=True,
    help="URLs of the files to download (can be passed multiple times).",
)
@click.option(
    "--model-folder",
    default=None,
    help="The folder of the model or component.",
)
@click.option(
    "--folder",
    default=None,
    help="Override folder within model-folder (optional).",
)
@click.pass_context
def cmd_download(
    ctx: click.Context,
    urls: tuple[str, ...],
    model_folder: str | None,
    folder: str | None,
) -> None:
    config = ctx.obj["config"]
    download_config = config.get("download", {})
    model_folder = model_folder or download_config.get("remote_models_folder")
    try:
        for url in urls:
            path = download_file(url, model_folder, folder)
            click.echo(f"Saved {url} to: {path}")
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command("mirror-copy", help="Mirror-copy models from source to destination with progress")
@click.argument("source", required=False, default=None)
@click.argument("destination", required=False, default=None)
@click.pass_context
def cmd_mirror_copy(
    ctx: click.Context,
    source: str | None,
    destination: str | None,
) -> None:
    config = ctx.obj["config"]
    mirror_copy_config = config.get("mirror-copy", {})
    general_config = config.get("general", {})
    source = source or mirror_copy_config.get("source")
    destination = destination or general_config.get("models_folder")
    try:
        mirror_copy(source, destination)
        click.echo("Mirror copy completed.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command("restore-settings", help="Restore ComfyUI settings")
@click.pass_context
def cmd_restore_settings(ctx: click.Context) -> None:
    config = ctx.obj["config"]
    try:
        restore_settings(config=config)
        click.echo("Settings restored successfully.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command("remove-unused", help="Remove unused models based on last access time")
@click.option(
    "--folder",
    default=r"C:/Users/adriano/Desktop/models",
    help="Folder to scan for unused models.",
)
@click.option(
    "--days",
    type=int,
    default=15,
    help="Minimum number of days since last access.",
)
def cmd_remove_unused(folder: str, days: int) -> None:
    try:
        remove_unused_models(folder, days)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


def main(argv: list[str] | None = None) -> int:
    try:
        exit_code = cli.main(args=argv, standalone_mode=False)
        return exit_code if exit_code is not None else 0
    except click.ClickException:
        raise
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
