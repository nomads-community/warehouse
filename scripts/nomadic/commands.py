import click
from metadata.metadata import ExpMetadataParser
from nomadic.dirs import ExperimentDirectories


@click.command(short_help="Create nomadic directory structure and copy metadata from a sequencing experiment")
@click.option(
    "-m",
    "--metadata_folder",
    type=str,
    required=True,
    help="Path to folder containing metadata CSV files."
)

@click.option(
    "-e",
    "--expt_id",
    type=str,
    required=True,
    help="Experiment ID. For example SLMM005."
)

def nomadic(metadata_folder, expt_id):
    """
    Create nomadic file structure including relevent metadata 
    """
    #Extract metadata
    exp_metadata = ExpMetadataParser(metadata_folder, expt_id)
    print("="*80)
    print(f"Experiment details for {exp_metadata.expt_id}")
    print(f"  Experiment date: {exp_metadata.expt_date}")
    print(f"  Experiment ID: {expt_id}")
    print(f"  Experiment Summary: {exp_metadata.expt_summary}")

    #Define experiment name    
    expt_name = create_experiment_name(exp_metadata.expt_date, expt_id, exp_metadata.expt_summary)
    
    #Create file hierarchy
    expt_dirs = create_nomadic_file_structure(expt_name)
    print("   Done")

    # Copying metadata
    print("Exporting metadata for nomadic...")
    exp_metadata.df.to_csv(f"{expt_dirs.metadata_dir}/sample_info.csv")
    print("Done.")
    print("="*80)

def create_experiment_name(expt_date: str, expt_id: str, expt_summary) -> str:
    """
    Create an experiment name from descriptive information

    """
    return f"{expt_date}_{expt_id.upper()}_{expt_summary}"

def create_nomadic_file_structure(expt_name: str):
    """
    Build the correct file hierarchy and return directory structure
    """
    print("Creating NOMADS experiment folder structure...")
    expt_dirs = ExperimentDirectories(expt_name)
    print(f"  Experiment: {expt_dirs.expt_dir}")
    print(f"  Metadata: {expt_dirs.metadata_dir}")
    print(f"  Guppy: {expt_dirs.guppy_dir}")
    print(f"  NOMADIC: {expt_dirs.nomadic_dir}")

    return expt_dirs