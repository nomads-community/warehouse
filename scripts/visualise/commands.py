import click
from pathlib import Path
from dash import Dash, html
from lib.general import check_file_present, Regex_patterns, identify_files_by_search
from metadata.metadata import ExpMetadataMerge, SampleMetadataParser, SequencingMetadataParser
from .layout import create_layout


@click.command(short_help="Dashboard to visualise summary data from NOMADS assays")

@click.option(
    "-s",
    "--sample_metadata_fn",
    type=Path,
    required=True,
    help="Path to csv file containing sample metadata information."
)

@click.option(
    "-m",
    "--metadata_folder",
    type=Path,
    required=True,
    help="Path to folder containing Excel metadata files from experiments."
)

@click.option(
    "-d",
    "--seqdata_folder",
    type=Path,
    required=True,
    help="Path to folder containing .csv outputs from Nomadic / Savannah."
)

def visualise(metadata_folder : Path, sample_metadata_fn : Path, seqdata_folder : Path ):

    print("Extracting experimental data")
    exp_fns = identify_files_by_search(metadata_folder, Regex_patterns.NOMADS_EXP_TEMPLATE)
    exp_class = ExpMetadataMerge(exp_fns, output_folder=None)

    print("Extracting sample metadata")
    check_file_present(sample_metadata_fn)
    sample_class = SampleMetadataParser(sample_metadata_fn, exp_class.rxns_df)
    print(f"   Found {sample_class.df.shape[0]} entries")
    print("="*80)

    print("Extracting sequence summary data")
    sequence_class= SequencingMetadataParser(seqdata_folder, exp_class.rxns_df)
    print("="*80)

    # OUTPUTS FOR NOTEBOOK ETC
    import os
    nb_folder = Path("./notebooks")
    exp_class.swga_df.to_csv(nb_folder.joinpath("rxn_swga_df.csv"),index=False)
    exp_class.pcr_df.to_csv(nb_folder.joinpath("rxn_pcr_df.csv"),index=False)
    exp_class.seqlib_df.to_csv(nb_folder.joinpath("rxn_seqlib_df.csv"),index=False)
    
    exp_class.rxns_df.to_csv(nb_folder.joinpath("rxn_metadata_df.csv"),index=False)
    exp_class.expts_df.to_csv(nb_folder.joinpath("exp_metadata_df.csv"),index=False)
    exp_class.all_df.to_csv(nb_folder.joinpath("exp_allmetadata_df.csv"),index=False)
    
    exp_class.swga_df.to_csv(nb_folder.joinpath("swga_df.csv"),index=False)
    exp_class.pcr_df.to_csv(nb_folder.joinpath("pcr_df.csv"),index=False)
    exp_class.seqlib_df.to_csv(nb_folder.joinpath("seqlib_df.csv"),index=False)

    sample_class.df.to_csv(nb_folder.joinpath("samples_df.csv"),index=False)
    sequence_class.summary_bam.to_csv(nb_folder.joinpath("seq_bam.csv"),index=False)
    sequence_class.summary_bedcov.to_csv(nb_folder.joinpath("seq_bedcov.csv"),index=False)

    print("Starting the warehouse dashboard")
    app = Dash()
    app.title = "Warehouse"
    app.layout = create_layout(app, sample_class, exp_class, sequence_class)
    app.run()

    # Summary of results with ability to stratify by a particular output eg sex?
    # Change nomadic to savannah call