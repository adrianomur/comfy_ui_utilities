import os
import subprocess


def mirror_copy_remote(source_folder, destination_folder):
    """
    Mirror-copy files from source_folder to destination_folder (can be remote).
    - Supports remote destinations in format: user@host:/path or host:/path
    - Uses rsync for efficient remote copying
    - Copies files and creates directories as needed
    - Skips copying if the destination file already exists with identical size and mtime
    - Removes files/dirs in destination that do not exist in source (true mirror)
    - Shows progress output from rsync

    Args:
        source_folder: Local source folder path
        destination_folder: Destination path (local or remote in format user@host:/path)
    """
    if not source_folder or not destination_folder:
        raise ValueError("Source and destination folders are required")

    if not os.path.isdir(source_folder):
        raise ValueError(
            f"Source folder does not exist or is not a directory: {source_folder}")

    # Ensure source folder ends with / for rsync to copy contents properly
    if not source_folder.endswith(os.sep):
        source_folder = source_folder + os.sep

    # Check if rsync is available
    try:
        subprocess.run(["rsync", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError(
            "rsync is not installed or not available in PATH. Please install rsync to use remote copying.")

    # Build rsync command
    # -a: archive mode (preserves permissions, timestamps, etc.)
    # -v: verbose
    # --progress: show progress
    # --delete: delete files in destination that don't exist in source (mirror behavior)
    # --human-readable: show sizes in human-readable format
    rsync_args = [
        "rsync",
        "-av",
        "--progress",
        "--delete",
        "--human-readable",
        source_folder,
        destination_folder
    ]

    print(f"Mirror copying from {source_folder} to {destination_folder}")
    print(f"Running: {' '.join(rsync_args)}")

    try:
        # Run rsync and capture output in real-time
        process = subprocess.Popen(
            rsync_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        # Print output line by line
        for line in process.stdout:
            print(line.rstrip())

        process.wait()

        if process.returncode != 0:
            raise RuntimeError(
                f"rsync failed with exit code {process.returncode}")

        print("Mirror copy completed successfully.")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"rsync command failed: {e}")
    except Exception as e:
        raise RuntimeError(f"Error during remote mirror copy: {e}")
