import logging
from pathlib import Path

import yaml

from warehouse.lib.general import (
    identify_all_folders_with_expid,
    identify_exptid_from_path,
    produce_dir,
)
from warehouse.lib.logging import divider, identify_cli_command
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
    log.info(divider)
    log.debug(identify_cli_command())

    # Read in the directory structure to create
    dir_yml = script_dir / "dir_structure.yml"
    with open(dir_yml, "r") as f:
        dirs = yaml.safe_load(f)

    # Get all ExpIDS from folders in the sequence folder
    seq_folders_with_expid = identify_all_folders_with_expid(seq_folder)
    exp_ids = [identify_exptid_from_path(e, False) for e in seq_folders_with_expid]
    for exp_id, exp in experiment_data.expdata_dict.items():
        # Must be a seqlib experiment
        if not exp.expt_type == "seqlib":
            continue
        # There must not be an exisiting folder referencing the same EXPID
        if exp_id in exp_ids:
            continue

        # Create the new folder
        new_folder_name = create_experiment_name(
            exp.expt_date, exp.expt_id, exp.expt_summary
        )
        seqfolder_path = seq_folder / new_folder_name
        produce_dir(seqfolder_path)
        # Populate with subdirectories
        for dir in dirs:
            target = seqfolder_path / dir
            produce_dir(target)
            if dir == "metadata":
                exp.df.to_csv(target / f"{exp_id}_sample_info.csv", index=False)


def create_experiment_name(expt_date: str, expt_id: str, expt_summary) -> str:
    """
    Create an experiment name from descriptive information

    """
    return f"{expt_date}_{expt_id.upper()}_{expt_summary}"
