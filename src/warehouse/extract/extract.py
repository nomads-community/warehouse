import logging
import os
import shutil
import subprocess
from pathlib import Path

from warehouse.lib.general import (
    identify_folders_by_pattern,
    is_directory_empty,
    produce_dir,
)

# Get logging process
log = logging.getLogger("extract")


def extract_outputs(
    source_dir: Path,
    target_dir: Path,
    exclusions: list,
    recursive: bool = False,
):
    """Copies contents of a folder to a new location.

    Args:
        source_dir(Path): The path to the source folder
        target_dir(Path): The path to the target folder
        recursive(bool): Copy top-level files or entire directory
    """
    # Starting entry
    rsync_components = ["rsync", "-zvrc"]

    # Add in exclusions:
    for exclusion in exclusions:
        rsync_components.extend(["--exclude", exclusion])

    # Add in folder exclusions
    if not recursive:
        rsync_components.extend(["--exclude", "*/"])

    # Complete the list:
    rsync_components.extend([source_dir, target_dir])

    # Give user feedback on the rsync command being run
    rsync_feedback = [
        f"{f.name}" if isinstance(f, Path) else f for f in rsync_components
    ]
    log.info(f"{" ".join(rsync_feedback)}")

    # Fromat the rsync command properly for bash to run it
    rsync_command = [
        f"{f.resolve()}/" if isinstance(f, Path) else f for f in rsync_components
    ]
    subprocess.run(rsync_command)
    log.info("")


def process_targets(
    targets: dict,
    source_base_dir: Path,
    target_base_dir: Path,
):
    """Iterates through a dictionary of targets and calls extract_outputs for each.

    Args:
        targets: A dictionary of target configurations. (key: target name, value: dict)
        source_base_dir: The base path for source directories.
        target_base_dir: The base path for target directories.
    """

    for _, target_config in targets.items():
        # Define source directory based on target name and source base
        target_name = target_config.get("name")
        source_dir = source_base_dir / target_name

        # Check if source directory exists and is not empty
        if not source_dir.exists() or is_directory_empty(source_dir):
            log.info(
                f"   {source_dir.name} is empty or does not exist. Skipping this target"
            )
            continue

        # Check if expected paths are given
        expected_path_dt = target_config.get("expected_path", {})
        # Pull in details from dict if given
        if expected_path_dt:
            path_type = expected_path_dt.get("type")
            pattern = expected_path_dt.get("pattern")

            log.debug(
                f"{target_name}: Expected path type: {path_type}, and pattern: {pattern}"
            )
            # Search for matching filepaths:
            found_paths = list(source_dir.glob(pattern))
            log.debug(f"Found: {found_paths}")
            # Warn if multiple or no matches
            if len(found_paths) == 0:
                log.warning(
                    f"   Expected path / pattern: {pattern} not found in {source_dir}"
                )
            if len(found_paths) > 1:
                pathnames = [p.name for p in found_paths]
                log.warning(
                    f"   Multiple expected {path_type}s: {pathnames} in {source_dir}, using first entry"
                )
            # Edit the source_dir if one or more (take the first) expected paths found to
            # account for different hierarchy
            if len(found_paths) > 0:
                source_dir = found_paths[0].parent
                log.debug(f"   Changed source_dir to: {source_dir}")

        # Define and create target directory based on target name and target base
        target_dir = target_base_dir / target_name
        produce_dir(target_dir)

        # Get recursive flag from target configuration
        recursive = target_config.get("copy_recursive", False)

        # Identify anything to exclude
        exclusions = target_config.get("copy_exclude", [])

        # Call extract_outputs for each target
        extract_outputs(source_dir, target_dir, exclusions, recursive)

        # Handle subfolders if present
        subfolders = target_config.get("subfolders", {})
        if subfolders:
            # Recursively process subfolders with appropriate source and target paths
            process_targets(subfolders, source_dir, target_dir)


def NOMADS_move_results(source_dir: Path, dest_dir: Path, symlink: bool = True):
    """
    Moves a folder from the source path to the destination path.

    Args:
      source_dir: The path to the folder to be moved.
      dest_dir: The path to the destination folder.
    """
    # Ensure correct filetypes
    if not isinstance(source_dir, Path):
        source_dir = Path(source_dir)
    if not isinstance(dest_dir, Path):
        dest_dir = Path(dest_dir)

    # Check if present
    if not source_dir.exists():
        raise FileNotFoundError(f"Path '{source_dir}' does not exist.")
    if not dest_dir.exists():
        raise FileNotFoundError(f"Path '{source_dir}' does not exist.")
    try:
        # Remove the dest_directory
        shutil.rmtree(str(dest_dir))
        # Move source to dest
        shutil.move(str(source_dir), str(dest_dir))
        if symlink:
            # Create a symlink
            os.symlink(str(dest_dir), str(source_dir))
            log.info("Folder moved successfully and symlink created.")
        log.info("Folder moved successfully.")
    except Exception as e:
        log.info(f"Error moving folder: {str(e)}")


def move_folder_optional_sudo_symlink(
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
        log.info("   Folder moved successfully.")

        if with_symlink:
            os.symlink(dest_dir, source_dir)
            log.info("   Symlink created")

    except subprocess.CalledProcessError as e:
        return f"   Error moving folder: {e}"


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
            print(f"   Error changing permissions for '{item}': {e}")


def identify_single_folder(folder_path: Path, pattern):
    """
    Identify a single target folder using a pattern and optionally test if empty

    Args:
      path: The path to the directory as a Path object.
      pattern: The pattern to search for.
    """
    folders = identify_folders_by_pattern(folder_path, pattern)

    if len(folders) != 1:
        return None

    return folders[0]
