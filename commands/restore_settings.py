import os
import shutil
import subprocess
import platform
from typing import Any
from config import load_config

# Project root (parent of commands/) for resolving comfy_ui.ico
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_COMFY_UI_ICO = "comfy_ui.ico"


def set_windows_folder_icon(folder_path: str, icon_path: str) -> None:
    """
    Set a custom icon for a folder on Windows using desktop.ini.
    Copies the icon into the folder and writes desktop.ini so Explorer displays it.
    """
    if platform.system() != "Windows" or not os.path.isfile(icon_path):
        return
    icon_name = os.path.basename(icon_path)
    dest_icon = os.path.join(folder_path, icon_name)
    if not os.path.exists(dest_icon) or not os.path.samefile(icon_path, dest_icon):
        shutil.copy2(icon_path, dest_icon)
    desktop_ini = os.path.join(folder_path, "desktop.ini")
    ini_content = (
        "[.ShellClassInfo]\r\n"
        f"IconResource={icon_name},0\r\n"
    )
    with open(desktop_ini, "w", encoding="utf-16") as f:
        f.write(ini_content)
    # Mark folder as read-only so Windows applies the custom icon (folder "read-only" = customized)
    subprocess.run(
        ["attrib", "+r", folder_path],
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

    # On Windows, set folder icon for source_path so Explorer displays it, then create symlink
    if platform.system() == "Windows":
        try:
            # Try with target_is_dir parameter (Python 3.8+)
            os.symlink(source_path, target_path, target_is_dir=True)
        except TypeError:
            # Fallback if target_is_dir is not supported - use mklink command
            subprocess.run(
                ["cmd", "/c", "mklink", "/D", target_path, source_path],
                check=True,
                shell=True
            )
        except OSError as e:
            if hasattr(e, 'winerror') and e.winerror == 1314:  # ERROR_PRIVILEGE_NOT_HELD
                raise OSError(
                    "Symlink creation failed. On Windows, you need either:\n"
                    "1. Administrator privileges, or\n"
                    "2. Developer Mode enabled (Settings > Update & Security > For developers)"
                ) from e
            raise
        except subprocess.CalledProcessError as e:
            # If mklink fails, provide helpful error message
            raise OSError(
                "Symlink creation failed. On Windows, you need either:\n"
                "1. Administrator privileges, or\n"
                "2. Developer Mode enabled (Settings > Update & Security > For developers)"
            ) from e
    else:
        # Linux and macOS
        os.symlink(source_path, target_path)

    return target_path


def create_run_nvidia_gpu_bat_file(nvidia_gpu_path: str, output_directory: str) -> str:
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

    icon_path = os.path.join(_PROJECT_ROOT, _COMFY_UI_ICO)
    set_windows_folder_icon(nvidia_gpu_path, icon_path)

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
            print(
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
        print(f"Installing requirements for {repo_name}...")
        pip_command = [python_path, "-m", "pip",
                       "install", "-r", requirements_file]
        subprocess.run(pip_command, check=True)
        print(f"Requirements installed for {repo_name}")
    else:
        print(
            f"No requirements.txt found for {repo_name}, skipping installation")


def install_requirements(repo_path: str, python_path: str) -> None:
    """
    Install requirements.txt if it exists using the specified Python pip.
    """
    repo_name = os.path.basename(repo_path)
    requirements_file = os.path.join(repo_path, "requirements.txt")
    if os.path.exists(requirements_file):
        print(f"Installing requirements for {repo_name}...")
        pip_command = [python_path, "-m", "pip",
                       "install", "-r", requirements_file]
        subprocess.run(pip_command, check=True)
        print(f"Requirements installed for {repo_name}")
    else:
        print(
            f"No requirements.txt found for {repo_name}, skipping installation")


def restore_settings(config: dict[str, Any]) -> None:
    """
    Restore the settings.json file to the confyui_path.
    """
    comfyui_folder = config.get("comfyui_folder")
    if not os.path.exists(comfyui_folder):
        raise FileNotFoundError(
            f"ComfyUI folder does not exist: {comfyui_folder}")
    if not os.path.isdir(comfyui_folder):
        raise ValueError(
            f"ComfyUI folder must be a directory: {comfyui_folder}")

    # Create a custom run_nvidia_gpu.bat file
    bat_file_path = os.path.join(comfyui_folder, "run_nvidia_gpu_custom.bat")
    custom_output_directory = config.get("output_directory")
    nvidia_gpu_path = create_run_nvidia_gpu_bat_file(bat_file_path, custom_output_directory)
    shortcut_path = config.get("shortcut_path")
    create_symlink(source_path=nvidia_gpu_path, target_path=shortcut_path)


    # Clone repos in custon nodes folder
    repositories = config.get("repositories", [])
    custom_nodes_path = os.path.join(comfyui_folder, "ComfyUI", "custom_nodes")
    python_path = os.path.join(comfyui_folder, "python_embeded", "python.exe")
    if not os.path.exists(python_path):
        raise FileNotFoundError(
            f"Python executable not found at: {python_path}. "
            f"Please ensure the embedded Python is installed."
        )
    for repo_url in repositories:
        clone_custom_nodes_repo(custom_nodes_path, repo_url, python_path)

    # Create model symlink
    source_models_path = config.get("model_folder")
    destination_models_path = os.path.join(comfyui_folder, "ComfyUI", "models")
    symlink_path = create_symlink(source_models_path, destination_models_path)

    # install requirements
    custom_nodes_path = os.path.join(comfyui_folder, "ComfyUI", "custom_nodes")
    for repo_name in os.listdir(custom_nodes_path):
        repo_path = os.path.join(custom_nodes_path, repo_name)
        install_requirements(repo_path, python_path)



def run() -> None:
    """
    Run the restore_settings command.
    """
    config = load_config()
    restore_settings_config = config.get("restore-settings", {})
    restore_settings(config=restore_settings_config)
