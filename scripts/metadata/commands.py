import click
import os
import re
from pathlib import Path
from lib.general import identify_fn_from_exptid

@click.command(short_help="Extract, validate and optionally export all metadata")
@click.option(
    "-m",
    "--metadata_folder",
    type=str,
    required=True,
    help="Path to folder containing Excel metadata files."
)

@click.option(
    "-o",
    "--output_folder",
    type=str,
    required=False,
    help="Output individual and aggregated metadata files."
)

@click.option(
    "-e",
    "--expt_id",
    type=str,
    required=False,
    default = "",
    help="Experiment ID. For example SLMM005."
    # callback=lambda ctx, param, value: validate_id(value) 
)

def metadata(metadata_folder, expt_id, output_folder):
    """
    Extract, combine and validate all metadata
    """

    from .metadata import ExpMetadataMerge
    from .metadata import ExpMetadataParser
    
    #Extract all metadata
    metadata_folder_path = Path(metadata_folder)
    if expt_id:
        #For an individual expt
        #Identify matching file
        matching_filepath = identify_fn_from_exptid(metadata_folder_path, expt_id)
        
        metadata = ExpMetadataParser(Path(matching_filepath.match_path))
        #Export data
        if output_folder:
                print(f"Outputting data to folder: {output_folder}")
                output_folder = Path(output_folder)
                #Expt
                expt_df = metadata.expt_df
                expt_fn = f"{expt_id}_expt_metadata.csv"
                expt_path = output_folder / expt_fn
                expt_df.to_csv(expt_path, index=False)
                #Reaction
                rxn_df = metadata.rxn_df
                rxn_fn = f"{expt_id}_rxn_metadata.csv"
                rxn_path = output_folder / rxn_fn
                rxn_df.to_csv(rxn_path, index=False)
                print("Done")
                print("="*80)   
    else:
        #For all files in folder
        #Find those that are correctly named
        fn_regex = '^\d{4}-\d{2}-\d{2}_(sWGA|PCR|SeqLib)_(SW|PC|SL)[a-zA-Z]{2}\d{3}_.*'
        matching_filepaths = { metadata_folder_path.joinpath(file) for file in os.listdir(metadata_folder) if re.match(fn_regex,file)}
        print(f"Found {len(matching_filepaths)} file(s)")
    
        #Extract all instances and merge data
        metadata = ExpMetadataMerge(matching_filepaths, output_folder) 

