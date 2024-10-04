import click
from pathlib import Path
from dash import Dash
from warehouse.lib.general import identify_files_by_search, check_path_present
from warehouse.lib.regex import Regex_patterns
from warehouse.metadata.metadata import (
    ExpMetadataMerge,
    SequencingMetadataParser,
    SampleMetadataParser,
    CombinedData,
)
from .layout import create_layout
# from warehouse.lib.controls import load_controls

CSS_STYLE = ["scripts/visualise/assets/calling-style.css"]


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
    "-c",
    "--sample_csv",
    type=Path,
    required=True,
    help="Path to csv file containing sample metadata information.",
)

@click.option(
    "-o",
    "--output_folder",
    type=Path,
    required=False,
    help="Output aggregated data for downstream analysis",
)

def visualise(exp_folder: Path, sample_csv: Path, seq_folder: Path, output_folder: Path = None):
    divider=("=" * 80)
    # print("Loading controls data")
    # controls = load_controls()
    # print("="*80)

    print("Extracting experimental data")
    exp_fns = identify_files_by_search(
        exp_folder, Regex_patterns.NOMADS_EXP_TEMPLATE, recursive=True
    )
    exp_data = ExpMetadataMerge(exp_fns, output_folder)

    print("Extracting sample data")
    check_path_present(sample_csv, isfile=True)
    sample_data = SampleMetadataParser(sample_csv, exp_data.rxns_df, output_folder)
    print(divider)
    
    print("Extracting sequence summary data")
    sequence_data = SequencingMetadataParser(seq_folder, exp_data, output_folder)
    print(divider)
    
    print("Combining data sources")
    combined_data = CombinedData(exp_data, sequence_data, sample_data, output_folder)
    print(divider)

    print("Starting the warehouse dashboard")
    app = Dash(__name__, external_stylesheets=CSS_STYLE)
    app.title = "Warehouse"
    app.layout = create_layout(app, sample_data, exp_data, sequence_data, combined_data)
    app.run()
