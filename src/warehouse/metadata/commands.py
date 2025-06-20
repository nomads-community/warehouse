import logging
from pathlib import Path

import click

from warehouse.lib.logging import divider, identify_cli_command
from warehouse.metadata.metadata import (
    Combine_Exp_Seq_Sample_data,
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
    "--sample_metadata_file",
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
    exp_folder: Path = None,
    seq_folder: Path = None,
    sample_metadata_file: Path = None,
    output_folder: Path = None,
):
    """
    Validate, merge and optionally export experimental and sequence data
    """

    # Set up child log and enter cli cmd
    log = logging.getLogger("metadata_commands")
    log.info(divider)
    log.debug(identify_cli_command())

    # Ensure some variables have been passed
    if not any([exp_folder, seq_folder, sample_metadata_file]):
        raise ValueError("Please supply -e, -m or -s inputs")

    if exp_folder:
        log.info("Processing experimental data")
        exp_data = ExpMetadataMerge(exp_folder, output_folder)

    if seq_folder:
        log.info("Processing sequencing data")
        seq_data = SequencingMetadataParser(seq_folder, output_folder)
        if exp_folder:
            seq_data.incorporate_experimental_data_to_sequence_class(exp_data)

    if sample_metadata_file:
        log.info("Processing sample metadata file")
        sample_data = SampleMetadataParser(sample_metadata_file, output_folder)
        if exp_folder:
            sample_data.incorporate_experimental_data_to_sampleclass(exp_data)

    if all([exp_folder, seq_folder, sample_metadata_file]):
        log.info("   Merging all data")
        Combine_Exp_Seq_Sample_data(exp_data, seq_data, sample_data, output_folder)
