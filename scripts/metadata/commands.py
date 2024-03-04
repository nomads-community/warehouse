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
        metadata = ExpMetadataParser(matching_filepath, output_folder)

    else:
        #For all files in folder that match NOMADS template naming:
        matching_filepaths = identify_nomads_files(metadata_folder)
        #Extract all instances and merge data
        metadata = ExpMetadataMerge(matching_filepaths, output_folder) 

