import logging
from pathlib import Path

import yaml

from warehouse.configure.configure import get_configuration_value
from warehouse.lib.general import (
    identify_all_folders_with_expid,
    produce_dir,
)
from warehouse.lib.logging import major_header
from warehouse.metadata.metadata import ExpDataMerge


def seqfolders(
    experiment_data: ExpDataMerge,
    seq_folder: Path,
):
    """
    Create NOMADS sequencing folder structure including relevent data
    """

    # Set up child log
    script_dir = Path(__file__).parent.resolve()
    log = logging.getLogger(script_dir.stem)
    major_header(log, "Creating sequence folders:")

    # Bool value to indicate if seqfolders have been created
    seqfolder_created = False

    # Read in the directory structure to create
    dir_yml = script_dir / "dir_structure.yml"
    with open(dir_yml, "r") as f:
        dirs = yaml.safe_load(f)

    # Get all exisiting seqfolder ExpIDS
    seq_folder_expids = identify_all_folders_with_expid(seq_folder)

    # Get all minknow, nomadic and savanna entries
    all_expids = []
    for target in ["nomadic_results_dir", "savanna_results_dir", "minknow_dir"]:
        value = get_configuration_value(target)
        exp_dict = identify_all_folders_with_expid(value)
        expids = [k for k, v in exp_dict.items() if not v.is_symlink()]
        log.debug(f"{target}: {value}, {exp_dict.keys()}, {expids}")
        all_expids = all_expids + expids
    # Make unique set
    all_expids = set(all_expids)

    for exp_id, exp in experiment_data.expdata_dict.items():
        # Must be a seqlib experiment
        if not exp.expt_type == "seqlib":
            continue
        # There must not be an existing folder referencing the same EXPID
        if exp_id in seq_folder_expids.keys():
            log.debug(f"Seqfolder for: {exp_id} already present")
            continue
        # Must have data from minknow / nomadic etc that references this EXPID
        # This prevents the creation of loads of empty directories on sequencing laptops
        if exp_id not in all_expids:
            log.debug(f"No local data for: {exp_id}, so no seqfolder created")
            continue
        log.debug(f"Creating seqfolder for: {exp_id}")
        # Create the new folder
        new_folder_name = create_experiment_name(
            exp.expt_date, exp.expt_id, exp.expt_summary
        )
        seqfolder_path = seq_folder / new_folder_name
        log.info(f"   Creating seqfolder: {seqfolder_path}")
        produce_dir(seqfolder_path)
        seqfolder_created = True
        # Populate with subdirectories
        for dir in dirs:
            target = seqfolder_path / dir
            produce_dir(target)
            if dir == "metadata":
                # Only export the minimum required information for end-user clarity
                min_info = [
                    exp.DataSchema.BARCODE[0],
                    exp.DataSchema.SAMPLE_ID[0],
                    exp.DataSchema.EXTRACTION_ID[0],
                    exp.DataSchema.SAMPLE_TYPE[0],
                ]
                exp.df[min_info].to_csv(
                    target / f"{exp_id}_sample_info.csv", index=False
                )
    if not seqfolder_created:
        log.info("   No new seqfolders created")


def create_experiment_name(expt_date: str, expt_id: str, expt_summary) -> str:
    """
    Create an experiment name from descriptive information

    """
    return f"{expt_date}_{expt_id.upper()}_{expt_summary}"
