import logging
from pathlib import Path

import click

from warehouse.configure.configure import get_configuration_value
from warehouse.lib.logging import divider, identify_cli_command
from warehouse.lib.synchronise import selective_rsync

script_dir = Path(__file__).parent.resolve()


@click.command(short_help="Backup sequence data folder to a local hard disk drive")
@click.option(
    "-b",
    "--backup_folder",
    type=Path,
    required=True,
    help="Path to backup folder on external USB drive",
)
@click.option(
    "-s",
    "--seq_folder",
    type=Path,
    help="Path to folder containing all sequencing data on local machine",
)
def backup(seq_folder: Path, backup_folder: Path) -> None:
    """
    Backup all sequence data files to a local USB drive.

    """
    # Read in from configuration if not supplied
    if not seq_folder:
        seq_folder = get_configuration_value("sequence")

    # Set up child log
    log = logging.getLogger(script_dir.stem + "_commands")
    log.info(divider)
    log.debug(identify_cli_command())
    log.info(f"Backing up sequence data from {seq_folder} to {backup_folder}")

    selective_rsync(
        source_dir=seq_folder,
        target_dir=backup_folder,
        recursive=True,
        delete=False,
    )
    log.info(divider)
