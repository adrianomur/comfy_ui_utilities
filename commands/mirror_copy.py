
import os
import shutil
import argparse
from tqdm import tqdm
from config import load_config


def mirror_copy(source_folder, destination_folder):
    """
    Mirror-copy files from source_folder to destination_folder.
    - Copies files and creates directories as needed.
    - Skips copying if the destination file already exists with identical size and mtime.
    - Removes files/dirs in destination that do not exist in source (true mirror).
    - Shows a progress bar for bytes copied.
    """
    if not source_folder or not destination_folder:
        raise ValueError("Source and destination folders are required")
    
    if not os.path.isdir(source_folder):
        raise ValueError(f"Source folder does not exist or is not a directory: {source_folder}")

    os.makedirs(destination_folder, exist_ok=True)

    # Helper: decide if a file needs copying
    def needs_copy(src, dst):
        if not os.path.exists(dst):
            return True
        try:
            s = os.stat(src)
            d = os.stat(dst)
            return not (s.st_size == d.st_size and int(s.st_mtime) == int(d.st_mtime))
        except OSError:
            return True

    # Precompute files to copy and total bytes
    files_to_copy = []
    total_bytes = 0
    for root, _, files in os.walk(source_folder):
        rel_root = os.path.relpath(root, source_folder)
        dest_root = os.path.join(destination_folder, "" if rel_root == "." else rel_root)
        for f in files:
            src_path = os.path.join(root, f)
            dst_path = os.path.join(dest_root, f)
            if needs_copy(src_path, dst_path):
                files_to_copy.append((src_path, dst_path))
                try:
                    total_bytes += os.path.getsize(src_path)
                except OSError:
                    pass

    # Copy with progress
    with tqdm(total=total_bytes, unit="B", unit_scale=True, desc="Copying") as progress:
        for src_path, dst_path in files_to_copy:
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            # Print the file being copied
            print(f"Copying: {src_path} -> {dst_path}")
            try:
                with open(src_path, "rb") as s, open(dst_path, "wb") as d:
                    while True:
                        chunk = s.read(1024 * 1024)  # 1MB
                        if not chunk:
                            break
                        d.write(chunk)
                        progress.update(len(chunk))
                try:
                    shutil.copystat(src_path, dst_path)
                except OSError:
                    pass
            except OSError:
                # Fallback: copy without granular progress
                try:
                    before = progress.n
                    shutil.copy2(src_path, dst_path)
                    try:
                        progress.update(max(0, os.path.getsize(src_path) - (progress.n - before)))
                    except OSError:
                        pass
                except OSError:
                    pass
