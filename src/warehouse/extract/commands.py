import logging
from pathlib import Path

import click
import yaml

from warehouse.lib.general import identify_all_folders
from warehouse.lib.logging import divider, identify_cli_command
from warehouse.lib.synchronise import (
    process_targets,
)

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
    required=True,
    help="Path to synchronisation folder where summary sequencing outputs should be copied to",
)
def extract(seq_folder: Path, output_folder: Path):
    """
    Extract summary sequence data files for sharing online

    """
    # Set up child log
    log = logging.getLogger("extract_commands")
    log.info(divider)
    log.debug(identify_cli_command())

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
