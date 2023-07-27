import click
import shutil
from lib.metadata import MetadataTableParser
from lib.inventory import InventoryUpdater
from lib.dirs import ExperimentDirectories
from lib.util import is_valid_format


EXPT_INVENTORY = "inventory/experiments.txt"
ASSAY_INVENTORY = "inventory/assays.txt"
SAMPLESET_INVENTORY = "inventory/sample_sets.txt"


def create_experiment_name(expt_date: str, expt_id: str, sample_set: str, assay: str) -> str:
    """
    Create an experiment name from dscriptive information

    """
    return f"{expt_date}_{sample_set.upper()}_{assay.upper()}_{expt_id.upper()}"



def main(expt_date, expt_id, sample_set, assay, metadata_csv):
    """
    Create folder structure for a given experiment
    
    """

    # Convert
    expt_id = expt_id.upper()
    sample_set = sample_set.upper()
    assay = assay.upper()

    # PARSE CLI
    print("Preparing data storage")
    is_valid_format(expt_date)
    print(f"  Experiment date: {expt_date}")
    print(f"  Experiment ID: {expt_id}")
    print(f"  Sample set: {sample_set}")
    print(f"  Assay: {assay}")
    print(f"  Metadata CSV: {metadata_csv}")
    print("")

    # UPDATE INVENTORIES
    print("Loading and updating inventories...")
    inventories = {
        "experiment": (EXPT_INVENTORY, expt_id),
        "assay": (ASSAY_INVENTORY, assay),
        "sample set": (SAMPLESET_INVENTORY, sample_set)
    }
    for name, (inv_path, inv_entry) in inventories.items():
        print(f"Updating {name} inventory at {inv_path}.")
        inv = InventoryUpdater(inv_path)
        inv.update(inv_entry)
    print("Done.")
    print("")

    # Next we check the metadata
    print("Loading and checking metadata...")
    print(f"  Input file: {metadata_csv}.")
    metadata_table = MetadataTableParser(metadata_csv)
    print("  Metadata passed formatting checks.")
    print(f"  Loaded {metadata_table.df.shape[0]} barcodes, each with {metadata_table.df.shape[1] - 1} fields.")
    print("Done.")
    print("")

    # Next make folders
    print("Creating experiment folder structure...")
    expt_name = create_experiment_name(expt_date, expt_id, sample_set, assay)
    expt_dirs = ExperimentDirectories(expt_name)
    print(f"  Experiment: {expt_dirs.expt_dir}")
    print(f"  Metadata: {expt_dirs.metadata_dir}")
    print(f"  Guppy: {expt_dirs.guppy_dir}")
    print(f"  NOMADIC: {expt_dirs.nomadic_dir}")
    print("Done.")
    print("")

    # Copying metadata
    print("Copying over metadata...")
    shutil.copy(src=metadata_table.csv, dst=f"{expt_dirs.metadata_dir}/sample_info.csv")
    print("Done.")
    print("")

    print("Process completed successfully.")
    print(f"Please move outputs from MinKNOW to: {expt_dirs.minknow_dir}")
    print("")


@click.command(short_help="Warehouse some NOMADS sequencing.")
@click.option(
    "-d",
    "--expt_date",
    type=str,
    required=True,
    help="Date experiment was conducted."
)
@click.option(
    "-e",
    "--expt_id",
    type=str,
    required=True,
    help="Experiment ID. For example MM-KP005."
)
@click.option(
    "-s",
    "--sample_set",
    type=str,
    required=True,
    help="Sample set ID. For example TES2022."
)
@click.option(
    "-a",
    "--assay",
    type=str,
    required=True,
    help="Assay ID. For example NOMADS8."
)
@click.option(
    "-m",
    "--metadata_csv",
    type=str,
    required=True,
    help="Path to metadata CSV."
)
def cli(expt_date, expt_id, sample_set, assay, metadata_csv):
    """
    Efficiently store sequencing data, automating the creation
    of directory structures, inventories, and validation of
    metadata
    
    """

    main(expt_date, expt_id, sample_set, assay, metadata_csv)


if __name__ == "__main__":
    cli()
         