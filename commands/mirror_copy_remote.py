import os
import subprocess
import re


def mirror_copy_remote(source_folder, destination_folder):
    """
    Mirror-copy files on a remote machine using SSH and rsync.
    SSHs into the remote machine and runs rsync from source_folder to destination_folder
    on that machine.

    Args:
        source_folder: Path on the remote machine to copy from
        destination_folder: Destination in format 'user@host:/path' where:
                           - user@host is the SSH connection info
                           - /path is the destination path on the remote machine
    """
    if not source_folder or not destination_folder:
        raise ValueError("Source and destination folders are required")

    # Parse destination to extract SSH connection info and remote path
    # Format: user@host:/path
    match = re.match(r'^([^@]+@[^:]+):(.+)$', destination_folder)
    if not match:
        raise ValueError(
            f"Destination must be in format 'user@host:/path', got: {destination_folder}"
        )

    ssh_connection = match.group(1)  # e.g., "adriano@frozen"
    # e.g., "/mnt/c/Users/adriano/Desktop/models"
    remote_destination = match.group(2)

    # Ensure source_folder is an absolute path
    if not source_folder.startswith('/'):
        raise ValueError(
            f"Source folder must be an absolute path, got: {source_folder}")

    # Ensure remote_destination is an absolute path
    if not remote_destination.startswith('/'):
        raise ValueError(
            f"Destination path must be an absolute path, got: {remote_destination}"
        )

    # Build the rsync command to run on the remote machine
    # rsync -av --delete source_folder/ destination_folder/
    # -a: archive mode (preserves permissions, timestamps, etc.)
    # -v: verbose
    # --delete: delete files in destination that don't exist in source (mirror behavior)
    rsync_cmd = [
        'rsync',
        '-av',
        '--delete',
        f'{source_folder.rstrip("/")}/',
        f'{remote_destination.rstrip("/")}/'
    ]

    # SSH into the machine and run rsync
    ssh_cmd = ['ssh', ssh_connection] + rsync_cmd

    print(f"Connecting to {ssh_connection}...")
    print(f"Running: rsync {' '.join(rsync_cmd)}")

    try:
        # Run the SSH command with rsync
        result = subprocess.run(
            ssh_cmd,
            check=True,
            capture_output=False,  # Show output in real-time
            text=True
        )
        print("Mirror copy completed successfully.")
        return result.returncode
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to execute rsync on remote machine: {e}"
        ) from e
    except FileNotFoundError:
        raise RuntimeError(
            "SSH command not found. Please ensure SSH is installed and available in PATH."
        )
