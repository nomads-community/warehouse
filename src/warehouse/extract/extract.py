from pathlib import Path
import subprocess
from warehouse.lib.general import produce_dir

def extract_outputs(source_dir: Path, target_dir: Path, recursive: bool = False):
    """Copies contents of a folder to a new location.

    Args:
        source_dir(Path): The path to the source folder
        target_dir(Path): The path to the target folder
        recursive(bool): Copy top-level files or entire directory
    """
    if recursive:
        rsync_components = ["rsync", "-zvrc", source_dir, target_dir]
    else:
        rsync_components = ["rsync", "-zvrc", "--exclude", "*/", source_dir, target_dir ]
        
    # Give user feedback on the rsync command being run
    rsync_feedback = [ f"{f.name}" if isinstance(f, Path) else f for f in rsync_components]
    print(f"{" ".join(rsync_feedback)}")

    # Fromat the rsync command properly for bash to run it
    rsync_command = [ f"{f.resolve()}/" if isinstance(f, Path) else f for f in rsync_components]
    subprocess.run(rsync_command)
    print("")
    

def process_targets(targets: dict, source_base_dir: Path, target_base_dir: Path):
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
            continue

        # Define and create target directory based on target name and target base
        target_dir = target_base_dir / target_name
        produce_dir(target_dir)

        # print(f"source_dir: {source_dir}, target: {target_dir}")
        # Get recursive flag from target configuration
        recursive = target_config.get("recursive", False)
        
        # Call extract_outputs for each target
        extract_outputs(source_dir, target_dir, recursive)
        
        # Handle subfolders if present
        subfolders = target_config.get("subfolders", {})
        if subfolders:
            # Recursively process subfolders with appropriate source and target paths
            process_targets(subfolders, source_dir, target_dir)