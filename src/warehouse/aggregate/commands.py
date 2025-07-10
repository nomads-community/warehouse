import logging
from pathlib import Path

import click
import pandas as pd
import yaml

from warehouse.aggregate.aggregate import aggregate_seq_data_to_single_dir
from warehouse.configure.configure import get_configuration_value
from warehouse.lib.general import identify_folders_by_pattern
from warehouse.lib.logging import divider, identify_cli_command
from warehouse.lib.regex import Regex_patterns

script_dir = Path(__file__).parent.resolve()


@click.command(short_help="Aggregate sequencing data into seqfolders structure")
@click.option(
    "-s",
    "--seq_folder",
    type=Path,
    help="Path to folder containing sequencing outputs generated with warehouse seqfolders",
)
@click.option(
    "-g",
    "--git_folder",
    type=Path,
    help="Path to git folder containing all NOMADS repositories",
)
def aggregate(seq_folder: Path, git_folder: Path):
    """
    Aggregate raw sequence data outputs into the standardised seqfolders structure
    """
    # Set up child log
    log = logging.getLogger(script_dir.stem + "_commands")
    log.info(divider)
    log.debug(identify_cli_command())

    # Read in from configuration if not supplied
    if not (seq_folder or git_folder):
        seq_folder = get_configuration_value("raw_sequence_folder")
        git_folder = get_configuration_value("git_folder")

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
        log.info(
            "The following experiments were processed (present indicates a not empty folder):"
        )
        log.info(summary_df.to_string(index=False))
    else:
        log.info("No experiments were identified for aggregation.")
    log.info(divider)
