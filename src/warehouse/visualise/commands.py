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
def visualise(exp_folder: Path, sample_csv: Path, seq_folder: Path):
    # print("Loading controls data")
    # controls = load_controls()
    # print("="*80)

    print("Extracting experimental data")
    exp_fns = identify_files_by_search(
        exp_folder, Regex_patterns.NOMADS_EXP_TEMPLATE, recursive=True
    )
    exp_data = ExpMetadataMerge(exp_fns)

    print("Extracting sample data")
    check_path_present(sample_csv, isfile=True)
    sample_data = SampleMetadataParser(sample_csv, exp_data.rxns_df)
    print(f"   with {sample_data.df.shape[0]} entries")
    print("=" * 80)

    print("Extracting sequence summary data")
    sequence_data = SequencingMetadataParser(seq_folder, exp_data)
    print("=" * 80)

    print("Combining data sources")
    combined_data = CombinedData(exp_data, sequence_data, sample_data)

    # OUTPUTS FOR NOTEBOOK ETC
    debug = False
    if debug:
        print("Exporting data for debugging")
        nb_folder = Path("./notebooks")
        exp_data.swga_df.to_csv(nb_folder.joinpath("rxn_swga_df.csv"), index=False)
        exp_data.pcr_df.to_csv(nb_folder.joinpath("rxn_pcr_df.csv"), index=False)
        exp_data.seqlib_df.to_csv(nb_folder.joinpath("rxn_seqlib_df.csv"), index=False)
        exp_data.rxns_df.to_csv(nb_folder.joinpath("rxns_df.csv"), index=False)
        exp_data.expts_df.to_csv(nb_folder.joinpath("exps_df.csv"), index=False)
        exp_data.all_df.to_csv(nb_folder.joinpath("exp_all_df.csv"), index=False)
        exp_data.swga_df.to_csv(nb_folder.joinpath("swga_df.csv"), index=False)
        exp_data.pcr_df.to_csv(nb_folder.joinpath("pcr_df.csv"), index=False)
        exp_data.seqlib_df.to_csv(nb_folder.joinpath("seqlib_df.csv"), index=False)
        sample_data.df.to_csv(nb_folder.joinpath("samples_df.csv"), index=False)
        sequence_data.summary_bam.to_csv(nb_folder.joinpath("seq_bam.csv"), index=False)
        sequence_data.summary_bedcov.to_csv(
            nb_folder.joinpath("seq_bedcov.csv"), index=False
        )

    print("Starting the warehouse dashboard")
    app = Dash(__name__, external_stylesheets=CSS_STYLE)
    app.title = "Warehouse"
    app.layout = create_layout(app, sample_data, exp_data, sequence_data, combined_data)
    app.run()
