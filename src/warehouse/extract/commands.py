import logging
from pathlib import Path

import click
import yaml

from warehouse.extract.extract import (
    identify_single_folder,
    move_folder_optional_sudo_symlink,
    process_targets,
)
from warehouse.lib.general import identify_all_folders, is_directory_empty
from warehouse.lib.logging import divider, identify_cli_command

script_dir = Path(__file__).parent.resolve()


@click.command(
    short_help="Consolidate sequencing data into seqfolders structure and selectively synchronise"
)
@click.option(
    "-s",
    "--seq_folder",
    type=Path,
    required=True,
    help="Path to folder containing sequencing outputs generated with warehouse seqfolders",
)
@click.option(
    "-o",
    "--output_folder",
    type=Path,
    required=False,
    help="Path to synchronisation folder where summary sequencing outputs should be copied to",
)
@click.option(
    "-i",
    "--expt_id",
    type=str,
    required=False,
    default="",
    help="Experiment ID (e.g. SLJS034) to consolidate data into sequencing folder",
)
@click.option(
    "-g",
    "--git_folder",
    type=Path,
    required=False,
    default=Path.home() / "git",
    help="Path to git folder containing nomadic and savanna clones",
)
def extract(seq_folder: Path, output_folder: Path, expt_id: str, git_folder: Path):
    """
    Consolidate sequence data summaries for sharing
    """
    # Set up child log
    log = logging.getLogger("extract_commands")
    log.info(divider)
    log.debug(identify_cli_command())

    # First try and consolidate all data into the standardised hierarchy
    if expt_id:
        # Identify and load targets dict from YAML file
        extractions_yaml = script_dir / "extractions.yaml"
        with open(extractions_yaml, "r") as f:
            extractions = yaml.safe_load(f)

        # User feedback
        log.info(f"Consolidating data for experiment {expt_id}")

        exp_folder = identify_single_folder(seq_folder, expt_id)
        if exp_folder:
            log.info(divider)
            for key_name, values in extractions.items():
                # Identify source_dir
                if values.get("git_prefix"):
                    source_dir = git_folder / values.get("source_dir")
                else:
                    source_dir = Path(values.get("source_dir"))
                source_dir = identify_single_folder(source_dir, f".*{expt_id}.*")
                if not source_dir:
                    log.info(f"   {key_name} source folder not found. Skipping.")
                    log.i
                    continue

                # Identify destination dir
                destination_dir = identify_single_folder(exp_folder, key_name)

                if not destination_dir:
                    log.info(f"   {key_name} destination folder not found. Skipping.")
                    continue

                if not is_directory_empty(destination_dir):
                    log.info(f"   {key_name} destination folder not empty. Skipping.")
                    continue

                # Give user feedback
                log.info(f"Source folder: {source_dir}")
                log.info(f"Destination folder: {destination_dir}")
                move_folder_optional_sudo_symlink(
                    source_dir,
                    destination_dir,
                    values.get("as_sudo"),
                    values.get("with_symlink"),
                )
                log.info(divider)
        else:
            log.info(f"   Experiment {expt_id} not found in {seq_folder}")
    log.info(divider)

    # Identify and load targets dict from YAML file
    yaml_file = script_dir / "targets.yaml"
    with open(yaml_file, "r") as f:
        targets = yaml.safe_load(f)

    # Build list of subfolders as a string for user feedback
    target_list = list(targets.keys())
    target_string = ", ".join(target_list[:-1]) + " and " + target_list[-1]

    log.info(
        f"Identifying sequence data summaries from {target_string} and copying them to the output folder:"
    )
    log.info(f"   Source: {seq_folder}")
    log.info(f"   Target: {output_folder}")

    # Identify all experimental folders
    exp_folders = [folder for folder in identify_all_folders(seq_folder)]

    for exp_folder in exp_folders:
        # Get the relative path
        relative_path = exp_folder.relative_to(seq_folder)
        target_folder = output_folder / relative_path

        # User feedback
        log.info("")
        log.info(divider)
        log.info(f"Copying {exp_folder.name}")
        log.info("")

        # Process
        process_targets(targets, exp_folder, target_folder)

    log.info(divider)
