import logging
import os
import re
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import yaml

from warehouse.lib.dataframes import tabulate_df
from warehouse.lib.general import (
    identify_exptid_from_path,
    identify_folders_by_pattern,
    identify_single_folder,
    is_directory_empty,
)
from warehouse.lib.logging import divider, identify_cli_command
from warehouse.lib.regex import Regex_patterns
from warehouse.lib.synchronise import chown_path_to_user_with_sudo

# Get logging process

script_dir = Path(__file__).parent.resolve()
log = logging.getLogger(script_dir.stem)


def aggregate(seq_folder: Path, git_folder: Path):
    """
    Aggregate raw sequence data outputs into the standardised seqfolders structure
    """
    # Set up child log
    log = logging.getLogger(script_dir.stem)
    log.debug(identify_cli_command())

    log.info(divider)
    log.info("Aggregating sequence data into sequence folders:")
    log.info(divider)

    # Identify and load targets dict from YAML file
    locations_yaml = script_dir / "locations.yml"
    with open(locations_yaml, "r") as f:
        locations = yaml.safe_load(f)

    # Define list of experiment folders
    expt_dirs = identify_folders_by_pattern(seq_folder, Regex_patterns.NOMADS_EXPID)

    summary_df = pd.DataFrame()
    # Process each folder
    for count, expt_dir in enumerate(expt_dirs):
        results, columns = aggregate_seq_data_to_single_dir(
            locations, expt_dir, git_folder
        )
        if count == 0:
            summary_df = pd.DataFrame(columns=columns)
        summary_df.loc[len(summary_df)] = results
        log.info(divider)

    if len(summary_df) > 0:
        log.info("The following experiments were processed:")
        log.info(tabulate_df(summary_df))
    else:
        log.info("No experiments were identified for aggregation.")
    log.info(divider)


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
            chown_path_to_user_with_sudo(dest_path)
        else:
            subprocess.run(["mv", source_dir, dest_dir], check=True)

        if with_symlink:
            os.symlink(dest_dir, source_dir)

    except subprocess.CalledProcessError as e:
        return f"   Error moving folder / creating symlink: {e}"


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
        # Ensure it is a not a symlink
        if source_dir.is_symlink():
            continue
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


def currently_sequencing() -> bool:
    """
    Prompts the user to input if they are currently performing a sequencing run or not.

    Returns:
        bool: True if the user indicates 'Yes' (Y or Enter), False if 'No' (N).
    """
    log.info("Are you currently sequencing? (Y/n - default is Y)")
    while True:
        try:
            choice = input("Y/n: ").strip().lower()
            if choice == "y" or choice == "":
                return True
            elif choice == "n":
                return False
            else:
                print(
                    "Invalid choice. Please enter 'Y' or 'N' (or just press Enter for 'Y')."
                )
        except Exception as e:  # Catch a more general exception for input issues
            log.error(f"An error occurred during input: {e}")
            print("An unexpected error occurred. Please try again.")
