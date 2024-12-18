import logging
import subprocess
from pathlib import Path

from warehouse.lib.general import (
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
                    f"   Expected path: {found_paths} not found in {source_dir}"
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
