import logging
from pathlib import Path

import click

from warehouse.lib.logging import divider, identify_cli_command
from warehouse.metadata.metadata import (
    ExpMetadataMerge,
    SampleMetadataParser,
    SequencingMetadataParser,
)


@click.command(
    short_help="Validate, merge and optionally export experimental and sequence data"
)
@click.option(
    "-e",
    "--exp_folder",
    type=Path,
    required=False,
    help="Path to folder containing completed experimental Excel template files.",
)
@click.option(
    "-s",
    "--seq_folder",
    type=Path,
    required=False,
    help="Path to folder containing sequencing outputs",
)
@click.option(
    "-m",
    "--metadata_file",
    type=Path,
    required=False,
    help="Path to file (csv or xlsx) containing sample metadata information.",
)
@click.option(
    "-o",
    "--output_folder",
    type=Path,
    required=False,
    help="Output individual and aggregated metadata files.",
)
def metadata(
    exp_folder: Path, seq_folder: Path, metadata_file: Path, output_folder: Path
):
    """
    Validate, merge and optionally export experimental and sequence data
    """

    # Set up child log and enter cli cmd
    log = logging.getLogger("metadata_commands")
    log.info(divider)
    log.debug(identify_cli_command())

    if exp_folder:
        log.info("Processing experimental data")
        exp_data = ExpMetadataMerge(exp_folder, output_folder)

    if seq_folder:
        log.info("Processing sequencing data")
        SequencingMetadataParser(seq_folder, output_folder)

    if metadata_file:
        log.info("Processing metadata file")
        sample_data = SampleMetadataParser(metadata_file, output_folder)
        if exp_folder:
            log.info("   Incorporating experimental metadata")
            sample_data.incorporate_experimental_data(exp_data, output_folder)
