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

        # Check if source directory exists
        if not source_dir.exists():
            log.info(f"   {source_dir.name} does not exist. Skipping this target")
            continue
        # Check if there are any files in the source
        if is_directory_empty(source_dir):
            log.info(f"   {source_dir.name} is empty. Skipping this target")
            continue
        # Check if the expected files are present
        expected_paths = target_config.get("expect", [])

        for expected_path in expected_paths:
            # Build path to check
            full_path = source_dir / expected_path
            # Try wildcard matching
            if "*" in expected_path:
                # Check if there are any matches
                found_paths = list(source_dir.glob(expected_path))
                if len(found_paths) > 0:
                    # Replace if a match was found
                    full_path = found_paths[0]

            if not full_path.exists():
                log.warning(
                    f"   Check File Hierarchy: {full_path.name} not found in {source_dir.name}."
                )

        # Define and create target directory based on target name and target base
        target_dir = target_base_dir / target_name
        produce_dir(target_dir)

        # Get recursive flag from target configuration
        recursive = target_config.get("recursive", False)

        # Identify anything to exclude
        exclusions = target_config.get("exclude", [])

        # Call extract_outputs for each target
        extract_outputs(source_dir, target_dir, exclusions, recursive)

        # Handle subfolders if present
        subfolders = target_config.get("subfolders", {})
        if subfolders:
            # Recursively process subfolders with appropriate source and target paths
            process_targets(subfolders, source_dir, target_dir)
