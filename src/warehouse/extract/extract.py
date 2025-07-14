import logging
from pathlib import Path

import yaml

from warehouse.configure.configure import get_configuration_value
from warehouse.lib.general import identify_all_folders
from warehouse.lib.logging import divider, identify_cli_command
from warehouse.lib.synchronise import (
    process_targets,
)

script_dir = Path(__file__).parent.resolve()


def extract(seq_folder: Path, output_folder: Path):
    """
    Extract summary sequence data files for sharing online

    """
    # Set up child log
    log = logging.getLogger(script_dir.stem)
    log.info(divider)
    log.debug(identify_cli_command())

    if not (seq_folder or output_folder):
        seq_folder = get_configuration_value("sequence_folder")
        output_folder = get_configuration_value("sequence")

    # Identify and load targets dict from YAML file
    yaml_file = script_dir / "targets.yml"
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
