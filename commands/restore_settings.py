import os
import shutil
import subprocess
import platform
from typing import Any
from config import load_config


def create_symlink(source_path: str, target_path: str) -> None:
    """
    Create a directory symlink from source_path to target_path.
    Works on Windows (requires admin or Developer Mode), Linux, and macOS.
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source path does not exist: {source_path}")
    if not os.path.isdir(source_path):
        raise ValueError(f"Source path must be a directory: {source_path}")

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

    # On Windows, symlinks require special handling for directories
    if platform.system() == "Windows":
        try:
            os.symlink(source_path, target_path, target_is_dir=True)
        except OSError as e:
            if e.winerror == 1314:  # ERROR_PRIVILEGE_NOT_HELD
                raise OSError(
                    "Symlink creation failed. On Windows, you need either:\n"
                    "1. Administrator privileges, or\n"
                    "2. Developer Mode enabled (Settings > Update & Security > For developers)"
                ) from e
            raise
    else:
        # Linux and macOS
        os.symlink(source_path, target_path)


def create_run_nvidia_gpu_bat_file(nvidia_gpu_path: str, output_directory: str) -> None:
    """
    Create a BAT file to run ComfyUI with NVIDIA GPU settings.
    """
    folder = os.path.dirname(nvidia_gpu_path)
    if not os.path.exists(folder):
        raise FileNotFoundError(f"Folder does not exist: {folder}")

    bat_content = (
        f".\\python_embeded\\python.exe -s ComfyUI\\main.py --windows-standalone-build --listen --output-directory {output_directory}\n"
        "pause\n"
    )

    if os.path.exists(nvidia_gpu_path):
        os.remove(nvidia_gpu_path)
        
    # Write the BAT file
    with open(nvidia_gpu_path, "w", encoding="utf-8") as f:
        f.write(bat_content)


def clone_custom_nodes_repo(custom_nodes_path: str, repo_url: str) -> None:
    """
    Clone the custom node repo.
    """
    subprocess.run(
        ["git", "clone", repo_url, custom_nodes_path],
        check=True
    )

    # Checkout main branch and pull (run in the cloned directory)
    subprocess.run(["git", "checkout", "main"], cwd=custom_nodes_path, check=True)
    subprocess.run(["git", "pull"], cwd=custom_nodes_path, check=True)


def restore_settings(config: dict[str, Any]) -> None:
    """
    Restore the settings.json file to the confyui_path.
    """
    comfyui_folder = config.get("comfyui_folder")
    if not os.path.exists(comfyui_folder):
        raise FileNotFoundError(f"ComfyUI folder does not exist: {comfyui_folder}")
    if not os.path.isdir(comfyui_folder):
        raise ValueError(f"ComfyUI folder must be a directory: {comfyui_folder}")

    # Create a custom run_nvidia_gpu.bat file
    bat_file_path = os.path.join(comfyui_folder, "run_nvidia_gpu_custom.bat")
    custom_output_directory = config.get("output_directory")
    create_run_nvidia_gpu_bat_file(bat_file_path, custom_output_directory)

    # Clone repos in custon nodes folder
    repositories = config.get("repositories", [])
    custom_nodes_path = os.path.join(comfyui_folder, "ComfyUI", "custom_nodes")
    for repo_url in repositories:
        clone_custom_nodes_repo(custom_nodes_path, repo_url)

    # Create model symlink
    source_models_path = config.get("model_folder")
    destination_models_path = os.path.join(comfyui_folder, "ComfyUI", "models")
    create_symlink(source_models_path, destination_models_path)


def run() -> None:
    """
    Run the restore_settings command.
    """
    config = load_config()
    restore_settings_config = config.get("restore-settings", {})
    restore_settings(config=restore_settings_config)
