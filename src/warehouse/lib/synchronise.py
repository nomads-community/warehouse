import logging
import os
import shutil
import subprocess
from pathlib import Path

from warehouse.lib.general import (
    is_directory_empty,
    produce_dir,
)

# Get logging process
log = logging.getLogger(Path(__file__).stem)


def selective_rsync(
    source_dir: Path,
    target_dir: Path,
    exclusions: list = None,
    recursive: bool = False,
    delete: bool = False,
    checksum: bool = False,
):
    """Copies contents of a folder to a new location.

    Args:
        source_dir(Path): The path to the source folder
        target_dir(Path): The path to the target folder
        exclusions(list): A list of file patterns to exclude
        recursive(bool): Copy top-level files or entire directory
        delete(bool): Delete files in target that are not in source
    """
    # Base command with compress (z), verbose (v), recursive (r)) and timestamp (t) options
    # r is needed to select all entries in the folder even if the rsync is not to be recursive
    # then a all folder exclusion is added
    rsync_components = ["rsync", "-zvrt"]

    # delete only works if recursive is True
    if recursive:
        rsync_components.append("--recursive")
        if delete:
            rsync_components.append("--delete")
    else:
        rsync_components.extend(["--exclude", "*/"])

    if checksum:
        rsync_components.append("--checksum")

    # Add in specific exclusions if given
    if exclusions:
        for exclusion in exclusions:
            rsync_components.extend(["--exclude", exclusion])

    # Complete the list:
    rsync_components.extend([source_dir, target_dir])

    # Give user feedback on the rsync command being run
    rsync_feedback = [
        f"{f.name}" if isinstance(f, Path) else f for f in rsync_components
    ]
    log.debug(f"{' '.join(rsync_feedback)}")
    try:
        # Format the rsync command properly for bash to run it
        rsync_command = [
            f"{f.resolve()}/" if isinstance(f, Path) else f for f in rsync_components
        ]
        result = subprocess.run(
            rsync_command, capture_output=True, text=True, check=True
        )
        if result.stdout:
            log.debug(f"stdout: {result.stdout}")
        if result.stderr:
            log.warning(f"stderr: {result.stderr}")
    except Exception as e:
        log.error(f"An unexpected error occurred: {e}")


def process_targets(
    targets: dict,
    source_base_dir: Path,
    target_base_dir: Path,
):
    """Iterates through a dictionary of targets and performs selective_rsync for each.

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
        if not source_dir.exists():
            log.debug(f"   {source_dir.name} does not exist. Skipping...")
            continue
        if is_directory_empty(source_dir):
            log.debug(f"   {source_dir.name} is empty. Skipping...")
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
        recursive = target_config.get("recursive", False)

        # Identify anything to exclude
        exclusions = target_config.get("exclusions", [])

        log.debug(f"   Rsyncing {target_name}")
        # rsync for each target
        selective_rsync(
            source_dir=source_dir,
            target_dir=target_dir,
            exclusions=exclusions,
            recursive=recursive,
        )

        # Handle subfolders if present
        subfolders = target_config.get("subfolders", {})
        if subfolders:
            # Process subfolders with appropriate source and target paths
            process_targets(
                targets=subfolders,
                source_base_dir=source_dir,
                target_base_dir=target_dir,
            )


def move_folder(
    source_path: Path,
    dest_path: Path,
    as_sudo: bool = False,
    with_symlink: bool = False,
) -> str:
    """
    Moves a folder with optional sudo privileges and replace with symlink in origin.

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
            log.warning(f"   Error changing permissions for '{item}': {e}")
