import click
from pathlib import Path
from lib.general import identify_nomads_files

@click.command(short_help="Extract, validate and optionally export all metadata")
@click.option(
    "-m",
    "--metadata_folder",
    type=Path,
    required=True,
    help="Path to folder containing Excel metadata files."
)

@click.option(
    "-o",
    "--output_folder",
    type=Path,
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

def metadata(metadata_folder : Path, expt_id : str, output_folder : Path):
    """
    Extract, combine and validate all metadata
    """

    from .metadata import ExpMetadataMerge
    from .metadata import ExpMetadataParser
    
    #Extract all metadata
    if expt_id:
        #For an individual expt identify the  matching file
        matching_filepath = identify_nomads_files(metadata_folder, expt_id)
        metadata = ExpMetadataParser(matching_filepath)
        #Export data
        if output_folder:
                print(f"Outputting data to folder: {output_folder.name}")
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
        #For all files in folder that match NOMADS template naming:
        matching_filepaths = identify_nomads_files(metadata_folder)
        #Extract all instances and merge data
        metadata = ExpMetadataMerge(matching_filepaths, output_folder) 

