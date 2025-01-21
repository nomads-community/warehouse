import logging
from pathlib import Path

import click

from warehouse.lib.general import (
    Regex_patterns,
    check_path_present_raise_error,
    identify_experiment_files,
    identify_files_by_search,
)
from warehouse.lib.logging import divider, identify_cli_command
from warehouse.metadata.metadata import (
    ExpMetadataMerge,
    ExpMetadataParser,
    SampleMetadataParser,
)


@click.command(
    short_help="Extract, validate and optionally export experimental data from completed NOMADS templates"
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
    required=False,
    default="",
    help="Experiment ID. For example SLJS034.",
)
@click.option(
    "-o",
    "--output_folder",
    type=Path,
    required=False,
    help="Output individual and aggregated metadata files.",
)
@click.option(
    "-m",
    "--metadata_file",
    type=Path,
    required=False,
    help="Path to file (csv or xlsx) containing sample metadata information.",
)
def metadata(exp_folder: Path, expt_id: str, output_folder: Path, metadata_file: Path):
    """
    Extract, combine and validate all metadata
    """

    # Set up child log and enter cli cmd
    log = logging.getLogger("metadata_commands")
    log.info(divider)
    log.debug(identify_cli_command())

    # Extract metadata from template file(s) if exptid defined
    if expt_id:
        # Search for file with exptid in name
        matching_filepaths = identify_experiment_files(exp_folder, expt_id)

        # Put outputs into subfolder experimental
        if output_folder:
            output_folder = output_folder / "experimental"

        ExpMetadataParser(matching_filepaths[0], output_folder)
        exit()
    else:
        matching_filepaths = identify_files_by_search(
            exp_folder, Regex_patterns.NOMADS_EXP_TEMPLATE, recursive=True
        )
        exp_data = ExpMetadataMerge(matching_filepaths, output_folder)

    # Must be used with an output option
    if metadata_file and output_folder:
        log.info("Extracting sample metadata")
        check_path_present_raise_error(metadata_file, isfile=True)
        SampleMetadataParser(metadata_file, exp_data.rxns_df, output_folder)
        log.info(divider)
