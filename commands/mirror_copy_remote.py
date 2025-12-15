import os
import subprocess
import re
import sys


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
    # rsync -av --delete --info=progress2 source_folder/ destination_folder/
    # -a: archive mode (preserves permissions, timestamps, etc.)
    # -v: verbose
    # --delete: delete files in destination that don't exist in source (mirror behavior)
    # --info=progress2: show overall progress with speed and percentage
    rsync_cmd = [
        'rsync',
        '-av',
        '--delete',
        '--info=progress2',
        f'{source_folder.rstrip("/")}/',
        f'{remote_destination.rstrip("/")}/'
    ]

    # SSH into the machine and run rsync
    ssh_cmd = ['ssh', ssh_connection] + rsync_cmd

    print(f"Connecting to {ssh_connection}...")
    print(f"Running: rsync {' '.join(rsync_cmd)}")
    print()

    try:
        # Run the SSH command with rsync and capture output for parsing
        process = subprocess.Popen(
            ssh_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )

        # Parse rsync progress output
        # Format: "    123,456,789  12%  123.45MB/s    0:00:12  (xfr#123, to-chk=456/789)"
        # The pattern matches: bytes, percentage, speed, time remaining, file counts
        progress_pattern = re.compile(
            r'\s+(\d+(?:,\d+)*)\s+(\d+)%\s+([\d.]+)([KMGT]?B)/s\s+(\d+:\d+:\d+)\s+\(xfr#(\d+),\s+to-chk=(\d+)/(\d+)\)'
        )

        last_line = ""

        while True:
            output_line = process.stdout.readline()
            if not output_line:
                break

            line = output_line.rstrip()

            # Check if this is a progress line
            match = progress_pattern.search(line)
            if match:
                percentage = match.group(2)
                speed = match.group(3)
                speed_unit = match.group(4)
                time_remaining = match.group(5)
                files_transferred = match.group(6)
                total_files = match.group(8)

                # Format the speed nicely
                speed_display = f"{speed}{speed_unit}/s"

                # Display progress with speed and percentage
                # Clear the line and write new progress
                sys.stdout.write(
                    f'\rProgress: {percentage}% | Speed: {speed_display} | Files: {files_transferred}/{total_files} | ETA: {time_remaining}')
                sys.stdout.flush()
                last_line = line
            else:
                # For non-progress lines, print them normally
                if line and not line.startswith('\r'):
                    # Clear progress line first if we had one
                    if last_line:
                        sys.stdout.write('\r' + ' ' * 100 + '\r')
                        sys.stdout.flush()
                    print(line)
                    last_line = ""

        # Wait for process to complete
        return_code = process.wait()

        # Clear the progress line
        sys.stdout.write('\r' + ' ' * 100 + '\r')
        sys.stdout.flush()

        if return_code == 0:
            print("Mirror copy completed successfully.")
        else:
            raise subprocess.CalledProcessError(return_code, ssh_cmd)

        return return_code
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to execute rsync on remote machine: {e}"
        ) from e
    except FileNotFoundError:
        raise RuntimeError(
            "SSH command not found. Please ensure SSH is installed and available in PATH."
        )
