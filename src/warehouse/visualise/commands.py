import logging
from pathlib import Path

import click
from dash import Dash

from warehouse.lib.general import (
    check_path_present_raise_error,
    identify_files_by_search,
)
from warehouse.lib.logging import divider
from warehouse.lib.regex import Regex_patterns
from warehouse.metadata.metadata import (
    CombinedData,
    ExpMetadataMerge,
    SampleMetadataParser,
    SequencingMetadataParser,
)
from warehouse.visualise.layout import create_layout

# from warehouse.lib.controls import load_controls

CSS_STYLE = ["scripts/visualise/assets/calling-style.css"]

# Define logging process
log = logging.getLogger("visualise")


@click.command(short_help="Dashboard to visualise summary data from NOMADS assays")
@click.option(
    "-e",
    "--exp_folder",
    type=Path,
    required=True,
    help="Path to folder containing completed experimental Excel template files.",
)
@click.option(
    "-s",
    "--seq_folder",
    type=Path,
    required=True,
    help="Path to folder containing outputs from Nomadic / Savannah.",
)
@click.option(
    "-m",
    "--metadata_file",
    type=Path,
    required=True,
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
    # Add in cli_flags
    cli_flags = [exp_folder, seq_folder, metadata_file]

    # divider=("=" * 80)
    # print("Loading controls data")
    # controls = load_controls()
    # print("="*80)

    log.info("Extracting experimental data")
    exp_fns = identify_files_by_search(
        exp_folder, Regex_patterns.NOMADS_EXP_TEMPLATE, recursive=True
    )
    exp_data = ExpMetadataMerge(exp_fns, output_folder)

    log.info("Extracting sample metadata")
    check_path_present_raise_error(metadata_file, isfile=True, raiseerror=True)
    sample_data = SampleMetadataParser(metadata_file, exp_data.rxns_df, output_folder)
    log.info(divider)

    log.info("Extracting sequence summary data")
    sequence_data = SequencingMetadataParser(seq_folder, exp_data, output_folder)
    log.info(divider)

    log.info("Combining data sources")
    combined_data = CombinedData(exp_data, sequence_data, sample_data, output_folder)
    log.info(divider)
    log.info("Starting the warehouse dashboard")

    app = Dash(__name__, external_stylesheets=CSS_STYLE)
    app.title = "Warehouse"
    app.layout = create_layout(
        app, sample_data, exp_data, sequence_data, combined_data, cli_flags
    )
    app.run()
