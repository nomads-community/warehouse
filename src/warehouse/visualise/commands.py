import logging
from pathlib import Path

import click
from dash import Dash

from warehouse.configure.configure import get_configuration_value
from warehouse.lib.logging import divider
from warehouse.metadata.metadata import (
    Combine_Exp_Seq_Sample_data,
    ExpMetadataMerge,
    SampleMetadataParser,
    SequencingMetadataParser,
)
from warehouse.visualise.layout import create_layout

CSS_STYLE = ["scripts/visualise/assets/calling-style.css"]

# Define logging process
log = logging.getLogger(Path(__file__).stem)


@click.command(short_help="Dashboard visualisation of NOMADS data from all experiments")
@click.option(
    "-e",
    "--exp_folder",
    type=Path,
    help="Path to folder containing completed experimental Excel template files.",
)
@click.option(
    "-s",
    "--seq_folder",
    type=Path,
    help="Path to folder containing outputs from Nomadic / Savannah.",
)
@click.option(
    "-m",
    "--metadata_file",
    type=Path,
    help="Path to file (csv or xlsx) containing sample metadata information.",
)
@click.option(
    "-o",
    "--output_folder",
    type=Path,
    required=False,
    help="Output aggregated data for downstream analysis",
)
def visualise(
    exp_folder: Path, metadata_file: Path, seq_folder: Path, output_folder: Path = None
):
    # Read in from configuration if not supplied
    if not exp_folder:
        exp_folder = get_configuration_value("experimental")
    if not seq_folder:
        seq_folder = get_configuration_value("sequence")
    if not metadata_file:
        metadata_file = get_configuration_value("metadata")

    # Add in cli_flags
    cli_flags = [exp_folder, seq_folder, metadata_file]

    log.info("Extracting experimental data")
    exp_data = ExpMetadataMerge(exp_folder, output_folder)
    log.info("Done")
    log.info(divider)

    log.info("Extracting sample metadata")
    sample_data = SampleMetadataParser(metadata_file, output_folder)
    sample_data.incorporate_experimental_data_to_sampleclass(exp_data)
    log.info("Done")
    log.info(divider)

    log.info("Extracting sequence summary data")
    seq_data = SequencingMetadataParser(seq_folder, output_folder)
    seq_data.incorporate_experimental_data_to_sequence_class(exp_data)
    log.info("Done")
    log.info(divider)

    log.info("Combining data sources")
    combined_data = Combine_Exp_Seq_Sample_data(
        exp_data, seq_data, sample_data, output_folder
    )
    log.info(divider)

    log.info("Starting the warehouse dashboard")
    app = Dash(__name__, external_stylesheets=CSS_STYLE)
    app.title = "Warehouse"
    app.layout = create_layout(
        app, sample_data, exp_data, seq_data, combined_data, cli_flags
    )
    app.run()
