import click
from lib.metadata import ExpMetadataParser
from lib.inventory import InventoryUpdater
from lib.dirs import ExperimentDirectories
from lib.util import is_valid_format


EXPT_INVENTORY = "inventory/experiments.txt"
ASSAY_INVENTORY = "inventory/assays.txt"
SAMPLESET_INVENTORY = "inventory/sample_sets.txt"


def create_experiment_name(expt_date: str, expt_id: str, sample_set: str, assay: str) -> str:
    """
    Create an experiment name from descriptive information

    """
    return f"{expt_date}_{sample_set.upper()}_{assay.upper()}_{expt_id.upper()}"



def main(expt_date, expt_id, sample_set, assay, metadata_table):
    """
    Create folder structure for a given experiment
    
    """

    # PARSE CLI / Metadata info
    print("Preparing data storage")
    is_valid_format(expt_date)
    print(f"  Experiment date: {expt_date}")
    print(f"  Experiment ID: {expt_id}")
    print(f"  Sample set: {sample_set}")
    print(f"  Assay: {assay}")
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
    print("Exporting metadata for nomadic...")
    metadata_table.to_csv(f"{expt_dirs.metadata_dir}/sample_info.csv")
    print("Done.")
    print("")

    print("Process completed successfully.")
    print(f"Please move outputs from MinKNOW to: {expt_dirs.minknow_dir}")
    print("")


@click.command(short_help="Warehouse NOMADS sequencing outputs systematically.")

@click.option(
    "-e",
    "--expt_id",
    type=str,
    required=True,
    help="Experiment ID. For example SLMM005."
)

@click.option(
    "-m",
    "--metadata_folder",
    type=str,
    required=True,
    help="Path to folder containing metadata CSV files."
)

def cli(expt_id, metadata_folder):
    """
    Efficiently store sequencing data, automating the creation
    of directory structures, inventories, and validation of
    metadata
    
    """
    print("Checking and extracting metadata...")
    exp_metadata = ExpMetadataParser(metadata_folder, expt_id)
    print("Done.")

    main(exp_metadata.expt_date, expt_id, "DANTESTING", "NOMADS8", exp_metadata.df)

if __name__ == "__main__":
    cli()
         
