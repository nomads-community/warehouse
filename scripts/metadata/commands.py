import click
from pathlib import Path
from lib.general import identify_files_by_search, Regex_patterns, identify_experiment_file

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
        #Search for file with exptid in name
        matching_filepath = identify_experiment_file(metadata_folder, expt_id)
        metadata = ExpMetadataParser(matching_filepath, output_folder)
    else:
        matching_filepaths = identify_files_by_search(metadata_folder, Regex_patterns.NOMADS_EXP_TEMPLATE)
        metadata = ExpMetadataMerge(matching_filepaths, output_folder)

