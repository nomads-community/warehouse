import click
import os
import re
import pandas as pd

@click.command(short_help="Combine and check all metadata files and export aggregate to csv in metadata folder")
@click.option(
    "-m",
    "--metadata_folder",
    type=str,
    required=True,
    help="Path to folder containing metadata CSV files."
)

@click.option(
    "-o",
    "--output",
    is_flag=True,
    show_default = True,
    help="Output merged metadata to aggregate CSVs in metadata folder."
)

def metadata(metadata_folder, output):
    """
    Combine and check all metadata files and export aggregate to csv in metadata folder
    """
    from .metadata import ExpMetadataParser
    from .metadata import ExpMetadataMerge
    
    print("Checking and extracting metadata...")
    print("="*80)

    #Identify all experiment ids
    fn_suffix = '_(expt|rxn)_metadata.csv'
    fn_prefix = '^(SW|PC|SL)[a-zA-Z]{2}\d{3}_'
    exp_ids = { re.sub(fn_suffix,"",file) for file in os.listdir(metadata_folder) if re.match(fn_prefix,file)}
    print(f"Found {len(exp_ids)} experiment ids")
    
    #Extract all instances, merge and output
    ExpMetadataMerge(metadata_folder, exp_ids)

    # For an individual experiment can:
    #  metadata = { expid: ExpMetadataParser(metadata_folder, expid) for expid in exp_ids }
    
    print("Done")
    print("="*80)