import os
import json
from datetime import datetime, timedelta


def last_time_files_read(folder: str) -> list[tuple[str, datetime]]:
    """
    Recursively list all files in a folder (excluding directories) and get their write/modification dates.

    Args:
        folder: Path to the folder to scan

    Returns:
        List of tuples containing (file_path, modification_datetime)
    """
    files_with_dates = []

    # Recursively walk through all directories and subdirectories
    for root, dirs, files in os.walk(folder):
        for file_name in files:
            filepath = os.path.join(root, file_name)
            try:
                stat_info = os.stat(filepath)
                # Use st_mtime for modification/write time (not st_atime for access time)
                modification_time = datetime.fromtimestamp(stat_info.st_atime)
                files_with_dates.append((filepath, modification_time))
                print(f"{filepath}: {modification_time}")
            except (OSError, PermissionError) as e:
                # Skip files that can't be accessed (permissions, broken symlinks, etc.)
                print(f"Warning: Could not access {filepath}: {e}")

    return files_with_dates


def get_paths_older_than(folder: str, days: int) -> list[tuple[str, datetime]]:
    """
    Get all paths in a folder that are older than a given number of days.
    """
    files_with_dates = last_time_files_read(folder)
    return [path for path, date in files_with_dates if date < datetime.now() - timedelta(days=days)]


def write_list_in_json(removed_models: list[str], folder: str):
    filename = os.path.join(folder, "removed_models.json")
    with open(filename, "w") as f:
        json.dump(removed_models, f)


def remove_unused_models(folder: str, days: int = 15):
    paths = get_paths_older_than(folder, days)
    removed_models = []
    for path in paths:
        # os.remove(path)
        removed_models.append(path)
    write_list_in_json(removed_models, folder)
    return removed_models

