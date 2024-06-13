import click
from pathlib import Path
from metadata.metadata import ExpMetadataParser
from nomadic.dirs import ExperimentDirectories
from lib.general import identify_experiment_file
from lib.exceptions import MetadataFormatError

@click.command(short_help="Create nomadic directory structure and copy metadata from a sequencing experiment")
@click.option(
    "-m",
    "--metadata_folder",
    type=Path,
    required=True,
    help="Path to folder containing Sequencing Library Excel files."
)

@click.option(
    "-e",
    "--expt_id",
    type=str,
    required=True,
    help="Experiment ID. For example SLMM005."
)

@click.option(
    "-o",
    "--output_folder",
    type=Path,
    required=False,
    help="Base folder to output experimental directory structure to."
)

@click.option(
    "-d",
    "--dir_structure",
    type=Path,
    required=False,
    help="Directory structure settings from .ini file."
)

def nomadic(metadata_folder : Path , expt_id : str, output_folder: Path, dir_structure: Path = None):
    """
    Create nomadic file structure including relevent metadata 
    """
    #Extract metadata
    matching_filepath = identify_experiment_file(metadata_folder, expt_id)
    exp_metadata = ExpMetadataParser(matching_filepath)
    print("="*80)

    #Make sure it is a seqlib expt
    if not exp_metadata.expt_type == "seqlib":
        raise MetadataFormatError(f"{matching_filepath.name} is not a seqlib expt")
    
    #Give user feedback
    print(f"Experiment details for {exp_metadata.expt_id}")
    print(f"  Experiment date: {exp_metadata.expt_date}")
    print(f"  Experiment ID: {expt_id}")
    print(f"  Experiment Summary: {exp_metadata.expt_summary}")
    print("="*80)

    #Define experiment name    
    expt_name = create_experiment_name(exp_metadata.expt_date, expt_id, exp_metadata.expt_summary)
    
    #Import data structure

    print("Creating NOMADS experiment folder structure...")
    expt_dirs = ExperimentDirectories(expt_name, output_folder, dir_structure)
    print("Done")
    print("="*80)

    # Copying metadata
    print("Exporting metadata for nomadic...")
    exp_metadata.df.to_csv(f"{expt_dirs.metadata_dir}/sample_info.csv", index=False)
    print("Done")
    print("="*80)

def create_experiment_name(expt_date: str, expt_id: str, expt_summary) -> str:
    """
    Create an experiment name from descriptive information

    """
    return f"{expt_date}_{expt_id.upper()}_{expt_summary}"