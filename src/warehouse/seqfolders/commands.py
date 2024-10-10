import click
from pathlib import Path
import logging

from warehouse.metadata.metadata import ExpMetadataParser
from warehouse.seqfolders.dirs import ExperimentDirectories
from warehouse.lib.general import identify_experiment_file
from warehouse.lib.exceptions import DataFormatError
from warehouse.lib.logging import identify_cli_command, divider


@click.command(
    short_help="Create appropriate NOMADS directory structure for a sequencing run"
)
@click.option(
    "-d",
    "--dir_structure",
    type=Path,
    required=False,
    help="Directory structure settings from .ini file.",
)
@click.option(
    "-e",
    "--exp_folder",
    type=Path,
    required=True,
    help="Path to folder containing completed experimental Excel template files.",
)
@click.option(
    "-i",
    "--expt_id",
    type=str,
    required=True,
    help="Experiment ID. For example SLJS034.",
)
@click.option(
    "-o",
    "--output_folder",
    type=Path,
    required=False,
    help="Base folder to output sequencing directory structure to.",
)
def seqfolders(
    exp_folder: Path, expt_id: str, output_folder: Path, dir_structure: Path = None
):
    """
    Create NOMADS sequencing folder structure including relevent data
    """
    #Set up child log
    log = logging.getLogger("seqfolders_commands")
    log.info(divider)
    log.debug(identify_cli_command())

    # Extract metadata
    matching_filepath = identify_experiment_file(exp_folder, expt_id)
    exp_metadata = ExpMetadataParser(matching_filepath)

    # Make sure it is a seqlib expt
    if not exp_metadata.expt_type == "seqlib":
        raise DataFormatError(f"{matching_filepath.name} is not a seqlib expt")

    # Give user feedback
    log.info(f"Experiment details for {exp_metadata.expt_id}")
    log.info(f"  Experiment date: {exp_metadata.expt_date}")
    log.info(f"  Experiment ID: {expt_id}")
    log.info(f"  Experiment Summary: {exp_metadata.expt_summary}")
    log.info("=" * 80)

    log.info("Creating NOMADS sequencing folder structure...")
    expt_name = create_experiment_name(
        exp_metadata.expt_date, expt_id, exp_metadata.expt_summary
    )
    expt_dirs = ExperimentDirectories(expt_name, output_folder, dir_structure)
    log.info("Done")
    log.info(divider)

    # Copying metadata
    log.info(
        "Exporting sequencing library information for downstream tools e.g. nomadic and savanna"
    )
    exp_metadata.df.to_csv(
        f"{expt_dirs.metadata_dir}/{expt_id}_sample_info.csv", index=False
    )
    log.info("Done")
    log.info(divider)


def create_experiment_name(expt_date: str, expt_id: str, expt_summary) -> str:
    """
    Create an experiment name from descriptive information

    """
    return f"{expt_date}_{expt_id.upper()}_{expt_summary}"
