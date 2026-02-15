import os
import shutil
import subprocess
import platform
from typing import Any
import click
from config import load_config

# Project root (parent of commands/) for resolving comfy_ui.ico
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_COMFY_UI_ICO = "comfy_ui.ico"


def set_windows_file_icon(file_path: str, icon_path: str) -> None:
    """
    Set a custom icon for a file on Windows.
    Set the icon_path on the file_path on Windows.
    """
    if platform.system() != "Windows":
        return

    for path in [file_path, icon_path]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"File does not exist: {path}")
        if not os.path.isfile(path):
            raise ValueError(f"File must be a file: {path}")

    # Set folder icon via desktop.ini so the folder containing file_path shows icon_path
    folder = os.path.dirname(os.path.abspath(file_path))
    desktop_ini_path = os.path.join(folder, "desktop.ini")
    icon_abs = os.path.abspath(icon_path)
    desktop_ini_content = (
        "[.ShellClassInfo]\r\n"
        f"IconResource={icon_abs},0\r\n"
        "InfoTip=ComfyUI\r\n"
    )
    with open(desktop_ini_path, "w", encoding="utf-8") as f:
        f.write(desktop_ini_content)
    subprocess.run(
        ["attrib", "+s", "+h", desktop_ini_path],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["attrib", "+r", folder],
        check=True,
        capture_output=True,
    )


def create_symlink(source_path: str, target_path: str) -> str:
    """
    Create a directory symlink from source_path to target_path.
    Works on Windows (requires admin or Developer Mode), Linux, and macOS.
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source path does not exist: {source_path}")

    # If target_path is already a symlink, remove it first
    if os.path.islink(target_path):
        os.unlink(target_path)
    # If target_path exists and is a directory, remove it to make way for symlink
    elif os.path.exists(target_path) and os.path.isdir(target_path):
        shutil.rmtree(target_path)
    # If target_path exists but is not a directory, raise error
    elif os.path.exists(target_path):
        raise FileExistsError(
            f"Target path already exists and is not a directory or symlink: {target_path}"
        )

    # On Windows, set folder icon for source_path so Explorer displays it, then create symlink
    if platform.system() == "Windows":
        os.symlink(source_path, target_path)
    
    click.echo(f"Symlink created: source_path: {source_path} -> target_path: {target_path}")
    return target_path


def create_run_nvidia_gpu_bat_file(nvidia_gpu_path: str, output_directory: str) -> str:
    """
    Create a BAT file to run ComfyUI with NVIDIA GPU settings.
    """
    folder = os.path.dirname(nvidia_gpu_path)
    if not os.path.exists(folder):
        raise FileNotFoundError(f"Folder does not exist: {folder}")

    bat_content = (
        "@echo off\n"
        'cd /d "%~dp0"\n'
        f".\\python_embeded\\python.exe -s ComfyUI\\main.py --windows-standalone-build --listen --output-directory {output_directory}\n"
        "pause\n"
    )

    if os.path.exists(nvidia_gpu_path):
        os.remove(nvidia_gpu_path)

    # Write the BAT file
    with open(nvidia_gpu_path, "w", encoding="utf-8") as f:
        f.write(bat_content)

    # icon_path = os.path.join(_PROJECT_ROOT, _COMFY_UI_ICO)
    # print(f"Setting Windows folder icon for {nvidia_gpu_path} with icon {icon_path}")
    # set_windows_file_icon(nvidia_gpu_path, icon_path)

    return nvidia_gpu_path


def clone_custom_nodes_repo(custom_nodes_path: str, repo_url: str, python_path: str) -> None:
    """
    Clone the custom node repo into a subdirectory within custom_nodes_path.
    If the directory already exists and is a git repo, pull instead of clone.
    Install requirements.txt if it exists using the specified Python pip.
    """
    # Extract repo name from URL (e.g., "ComfyUI-Manager" from "https://github.com/Comfy-Org/ComfyUI-Manager.git")
    repo_name = os.path.basename(repo_url).replace(".git", "")
    repo_path = os.path.join(custom_nodes_path, repo_name)

    # Ensure custom_nodes directory exists
    os.makedirs(custom_nodes_path, exist_ok=True)

    # Check if the repo directory already exists
    if os.path.exists(repo_path):
        # Check if it's a git repository
        git_dir = os.path.join(repo_path, ".git")
        if os.path.exists(git_dir):
            # It's already a git repo, pull instead of clone
            click.echo(
                f"Repository {repo_name} already exists, pulling latest changes...")
            subprocess.run(["git", "pull"], cwd=repo_path, check=True)
        else:
            # Directory exists but is not a git repo - raise an error
            raise ValueError(
                f"Directory {repo_path} already exists but is not a git repository. "
                f"Please remove it manually or choose a different location."
            )
    else:
        # Clone the repository
        subprocess.run(
            ["git", "clone", repo_url, repo_path],
            check=True
        )

        # Checkout main branch and pull (run in the cloned directory)
        subprocess.run(["git", "pull"], cwd=repo_path, check=True)

    # Install requirements if requirements.txt exists
    requirements_file = os.path.join(repo_path, "requirements.txt")
    if os.path.exists(requirements_file):
        click.echo(f"Installing requirements for {repo_name}...")
        pip_command = [python_path, "-m", "pip",
                       "install", "-r", requirements_file]
        subprocess.run(pip_command, check=True)
        click.echo(f"Requirements installed for {repo_name}")
    else:
        click.echo(
            f"No requirements.txt found for {repo_name}, skipping installation")


def install_requirements(repo_path: str, python_path: str) -> None:
    """
    Install requirements.txt if it exists using the specified Python pip.
    """
    repo_name = os.path.basename(repo_path)
    requirements_file = os.path.join(repo_path, "requirements.txt")
    if os.path.exists(requirements_file):
        click.echo(f"Installing requirements for {repo_name}...")
        pip_command = [python_path, "-m", "pip",
                       "install", "-r", requirements_file]
        subprocess.run(pip_command, check=True)
        click.echo(f"Requirements installed for {repo_name}")
    else:
        click.echo(
            f"No requirements.txt found for {repo_name}, skipping installation")


def restore_settings(config: dict[str, Any]) -> None:
    """
    Restore the settings.json file to the confyui_path.
    """
    config_general = config.get("general")
    comfy_ui_folder = config_general.get("comfyui_folder")
    if not os.path.exists(comfy_ui_folder):
        raise FileNotFoundError(
            f"ComfyUI folder does not exist: {comfy_ui_folder}")
    if not os.path.isdir(comfy_ui_folder):
        raise ValueError(
            f"ComfyUI folder must be a directory: {comfy_ui_folder}")

    # Create a run_nvidia_gpu_custom.bat file
    nvidia_gpu_path = os.path.join(comfy_ui_folder, "run_nvidia_gpu_custom.bat")
    custom_output_directory = config_general.get("outputs_directory")
    nvidia_gpu_path = create_run_nvidia_gpu_bat_file(nvidia_gpu_path, custom_output_directory)
    
    # Set shortcut from the run_nvidia_gpu_custom.bat file
    restore_settings_config = config.get("restore-settings", {})
    shortcut_path = restore_settings_config.get("shortcut_path", {})
    if shortcut_path is None:
        click.echo("Shortcut path is not set in the restore-settings section of the config.json file, skipping shortcut creation")
    else:
        create_symlink(source_path=nvidia_gpu_path, target_path=shortcut_path)
    
    # Clone repos in custon nodes folder
    repositories = restore_settings_config.get("repositories", [])
    custom_nodes_path = os.path.join(comfy_ui_folder, "ComfyUI", "custom_nodes")
    python_path = os.path.join(comfy_ui_folder, "python_embeded", "python.exe")
    if not os.path.exists(python_path):
        raise FileNotFoundError(
            f"Python executable not found at: {python_path}. "
            f"Please ensure the embedded Python is installed."
        )
    for repo_url in repositories:
        clone_custom_nodes_repo(custom_nodes_path, repo_url, python_path)

    # Create model symlink
    source_models_path = config.get("general").get("models_folder")
    destination_models_path = os.path.join(comfy_ui_folder, "ComfyUI", "models")
    create_symlink(source_models_path, destination_models_path)

    # Create workflows symlink
    source_workflows_path = config.get("restore-settings").get("workflows_path")
    workflows_path = os.path.join(comfy_ui_folder, "ComfyUI", "user", "default", "workflows")
    create_symlink(source_workflows_path, workflows_path)
    
    # Install requirements in custom nodes
    custom_nodes_path = os.path.join(comfy_ui_folder, "ComfyUI", "custom_nodes")
    for repo_name in os.listdir(custom_nodes_path):
        repo_path = os.path.join(custom_nodes_path, repo_name)
        install_requirements(repo_path, python_path)


def run(config: dict[str, Any] | None = None) -> None:
    """
    Run the restore_settings command.
    If config is not provided, it is loaded from the default config file.
    """
    if config is None:
        config = load_config()
    restore_settings(config=config)
