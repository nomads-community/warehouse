import logging
from pathlib import Path

import click

from warehouse.lib.exceptions import DataFormatError
from warehouse.lib.general import identify_experiment_files
from warehouse.lib.logging import divider, identify_cli_command
from warehouse.metadata.metadata import ExpMetadataMerge, ExpMetadataParser
from warehouse.seqfolders.dirs import ExperimentDirectories


@click.command(
    short_help="Generate NOMADS directory structure for a sequencing run from NOMADS metadata"
)
@click.option(
    "-e",
    "--exp_folder",
    type=Path,
    required=True,
    help="Path to folder containing completed experimental Excel template files.",
)
@click.option(
    "-i",
    "--expt_id",
    type=str,
    required=True,
    help="Experiment ID. For example SLJS034.",
)
@click.option(
    "-o",
    "--output_folder",
    type=Path,
    required=False,
    help="Base folder to output sequencing directory structure to.",
)
@click.option(
    "-d",
    "--dir_structure",
    type=Path,
    required=False,
    help="Directory structure settings from .ini file.",
)
def seqfolders(
    exp_folder: Path, expt_id: str, output_folder: Path, dir_structure: Path = None
):
    """
    Create NOMADS sequencing folder structure including relevent data
    """
    # Set up child log
    log = logging.getLogger("seqfolders_commands")
    log.info(divider)
    log.debug(identify_cli_command())

    # First extract the individual experiment
    seqlib_fn = identify_experiment_files(exp_folder, expt_id)
    exp_metadata = ExpMetadataParser(seqlib_fn[0])

    # Make sure it is a seqlib expt
    if not exp_metadata.expt_type == "seqlib":
        raise DataFormatError(f"{seqlib_fn.name} is not a seqlib expt")

    # Give user feedback
    log.info(f"Experiment details for {exp_metadata.expt_id}")
    log.info(f"  Experiment date: {exp_metadata.expt_date}")
    log.info(f"  Experiment Summary: {exp_metadata.expt_summary}")
    log.info("=" * 80)

    log.info(f"Creating NOMADS sequencing folder structure for {expt_id}...")
    expt_name = create_experiment_name(
        exp_metadata.expt_date, expt_id, exp_metadata.expt_summary
    )
    expt_dirs = ExperimentDirectories(expt_name, output_folder, dir_structure)
    log.info("Done")
    log.info(divider)

    # Copying metadata
    log.info(f"Identifying all metadata for samples included in {expt_id}")
    # this is needed to extract information entered in an earlier template
    # e.g. during pcr or swga that is not copied into the library template

    # First extract all identifiers from swga_identifier and pcr_identifier columns
    identifiers = exp_metadata.rxn_df["swga_identifier"].dropna().unique().tolist()
    identifiers.extend(exp_metadata.rxn_df["pcr_identifier"].dropna().unique().tolist())

    # strip out the well info and create unique set of expids
    expids = list([id[:-3] for id in identifiers if "swga" not in id.lower()])
    # Add in the current experiment id
    if expt_id in expids:
        raise DataFormatError(f"{expt_id} is being used as an sWGA or PCR identifier")
    # Create a list of unique expids that need to be extracted
    expids = set(expids + [expt_id])

    matching_filepaths = identify_experiment_files(exp_folder, expids)

    # Extract all data
    exp_metadata = ExpMetadataMerge(matching_filepaths)

    # Filter to the exptid given by user and sort by barcode column
    exp_metadata_df = exp_metadata.all_df[
        exp_metadata.all_df["expt_id_seqlib"] == expt_id
    ].sort_values(by="barcode")

    # Export as sample_info file
    exp_metadata_df.to_csv(
        f"{expt_dirs.metadata_dir}/{expt_id}_sample_info.csv", index=False
    )
    log.info("Done")
    log.info(divider)


def create_experiment_name(expt_date: str, expt_id: str, expt_summary) -> str:
    """
    Create an experiment name from descriptive information

    """
    return f"{expt_date}_{expt_id.upper()}_{expt_summary}"
