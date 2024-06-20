import click
from pathlib import Path
from lib.general import identify_files_by_search, Regex_patterns, identify_experiment_file

@click.command(short_help="Extract, validate and optionally export experimental data")

@click.option(
    "-e",
    "--exp_folder",
    type=Path,
    required=True,
    help="Path to folder containing completed experimental Excel template files."
)

@click.option(
    "-i",
    "--expt_id",
    type=str,
    required=False,
    default = "",
    help="Experiment ID. For example SLJS034."
)

@click.option(
    "-o",
    "--output_folder",
    type=Path,
    required=False,
    help="Output individual and aggregated metadata files."
)

def metadata(exp_folder : Path, expt_id : str, output_folder : Path):
    """
    Extract, combine and validate all metadata
    """

    from .metadata import ExpMetadataMerge
    from .metadata import ExpMetadataParser
    
    #Extract all metadata
    if expt_id:
        #Search for file with exptid in name
        matching_filepath = identify_experiment_file(exp_folder, expt_id)
        metadata = ExpMetadataParser(matching_filepath, output_folder)
    else:
        matching_filepaths = identify_files_by_search(exp_folder, Regex_patterns.NOMADS_EXP_TEMPLATE, recursive=True)
        metadata = ExpMetadataMerge(matching_filepaths, output_folder)

