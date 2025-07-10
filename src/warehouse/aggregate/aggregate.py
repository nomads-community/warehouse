import logging
import os
import re
import shutil
import subprocess
from pathlib import Path

from warehouse.lib.general import (
    identify_exptid_from_path,
    identify_single_folder,
    is_directory_empty,
)

# Get logging process

script_dir = Path(__file__).parent.resolve()
log = logging.getLogger(script_dir.stem)


def move_folder(
    source_path: Path,
    dest_path: Path,
    as_sudo: bool = False,
    with_symlink: bool = False,
) -> str:
    """
    Moves a folder using the 'sudo' command.

    Args:
      source_dir: The path to the folder to be moved.
      dest_dir: The path to the destination folder.

    Returns:
      A string indicating success or the error message.
    """
    try:
        # Convert pathlib objects to str
        source_dir = str(source_path.resolve())
        dest_dir = str(dest_path.resolve())

        # Remove the dest_directory
        shutil.rmtree(dest_dir)
        # Move source to dest
        if as_sudo:
            subprocess.run(["sudo", "mv", source_dir, dest_dir], check=True)
            chown_paths_to_user(dest_path)
        else:
            subprocess.run(["mv", source_dir, dest_dir], check=True)

        if with_symlink:
            os.symlink(dest_dir, source_dir)

    except subprocess.CalledProcessError as e:
        return f"   Error moving folder / creating symlink: {e}"


def chown_paths_to_user(path: Path):
    """
    Recursively change ownership of files / folders within a path.

    Args:
      path: The path to the directory as a Path object.
    """
    user = os.getlogin()
    dir = str(path.resolve())
    subprocess.run(["sudo", "chown", f"{user}:{user}", dir], check=True)
    for path_ob in path.rglob("*"):
        try:
            item = str(path_ob.resolve())
            subprocess.run(["sudo", "chown", f"{user}:{user}", item], check=True)
        except OSError as e:
            log.info(f"   Error changing permissions for '{item}': {e}")


def aggregate_seq_data_to_single_dir(
    locations: dict, expt_dir: Path, git_folder: Path
) -> list:
    """
    Check presence of expected folders (whether full) and then move to expt_folder.

    Args:
        locations: A dictionary containing the transfer specifics.
        expt_dir: The path to the experiment directory.
        git_folder: The path to the git folder.


    """
    # Get the expt_id for the path
    expt_id = identify_exptid_from_path(expt_dir, raise_error=False)
    if not expt_id:
        log.info(f"   Experiment ID not found in path: {expt_dir}. Skipping...")
        return

    log.info(f"Aggregating data for experiment {expt_id} into {expt_dir}")

    # Record outcomes for each process with columns:
    # expt_id, target1, target 2...
    columns = ["Experiment ID"]
    results = [expt_id]

    # Process each target in the locations dict
    for key_name, values in locations.items():
        columns.append(key_name)
        # Identify destination dir and ensure empty
        destination_dir = expt_dir / key_name
        log.debug(f"destination_dir: {destination_dir}")

        if not destination_dir.exists():
            log.info(f"   {key_name} destination folder not found. Skipping...")
            results.append("Destination Missing")
            continue
        if not is_directory_empty(destination_dir, raise_error=False):
            log.info(f"   {key_name} destination folder not empty. Skipping...")
            results.append("Present")
            continue

        # Identify source_dir
        if values.get("git_prefix"):
            source_dir = git_folder / values.get("source_dir")
        else:
            source_dir = Path(values.get("source_dir"))
        log.debug(f"source_dir: {source_dir}")

        source_dir = identify_single_folder(
            folder_path=source_dir,
            pattern=re.compile(f".*{expt_id}.*"),
            recursive=False,
        )
        if not source_dir:
            log.info(f"   {key_name} source folder not found. Skipping...")
            results.append("Source Missing")
            continue

        # Build the command
        as_sudo = values.get("as_sudo")
        with_symlink = values.get("with_symlink")
        # Give user feedback
        log.info(f"   {key_name} folders found.")
        move_folder(
            source_dir,
            destination_dir,
            as_sudo,
            with_symlink,
        )
        msg = "Moved"
        if with_symlink:
            msg = f"{msg} and symlinked"
        log.info(f"      {msg}: {source_dir} -> {destination_dir}")
        results.append(msg)

    return results, columns
