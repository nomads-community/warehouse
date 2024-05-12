import click
from pathlib import Path
import pandas as pd
from lib.general import check_file_present, Regex_patterns, identify_files_by_search
from metadata.metadata import ExpMetadataMerge, SampleMetadataExtract

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
    print("")
    matching_filepaths = identify_files_by_search(metadata_folder, Regex_patterns.NOMADS_EXP_TEMPLATE)
    exp_metadata = ExpMetadataMerge(matching_filepaths, output_folder=None)

    print("Extracting sample metadata")
    check_file_present(sample_metadata_fn)
    sample_metadata = SampleMetadataExtract(sample_metadata_fn)
    print(f"   Found {sample_metadata.df.shape[0]} entries")
    print("="*80)

    print("Extracting sequence summary data")
    seqdata = identify_files_by_search(seqdata_folder, Regex_patterns.SEQDATASUMMARY_CSV)
    print(seqdata)

    # OUTPUTS FOR NOTEBOOK ETC

    # exp_metadata.swga_df.to_csv("rxn_swga_df.csv")
    # exp_metadata.pcr_df.to_csv("rxn_pcr_df.csv")
    # exp_metadata.seqlib_df.to_csv("rxn_seqlib_df.csv")
    
    # exp_metadata.rxn_metadata_df.to_csv("rxn_metadata_df.csv")
    # exp_metadata.expt_metadata_df.to_csv("exp_metadata_df.csv")
    # exp_metadata.allmetadata_df.to_csv('allmetadata_df.csv')
    # print("="*80)
    #Build a bar chart of the aggregate data
    
    # Combine all data and filter results to samples
    # Can we run bamboo by default?
    # Dashboard to show
    # Summary of numbers run for each stage eg swga etc
    # Summary of results with ability to stratify by a particular output eg sex?
    # Change nomadic to savannah call
