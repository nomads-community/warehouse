import logging
from pathlib import Path

import click

from warehouse.lib.logging import divider, identify_cli_command
from warehouse.lib.synchronise import selective_rsync

script_dir = Path(__file__).parent.resolve()


@click.command(short_help="Backup sequence data folder to a local hard disk drive")
@click.option(
    "-s",
    "--seq_folder",
    type=Path,
    required=True,
    help="Path to folder containing all sequencing data on local machine",
)
@click.option(
    "-b",
    "--backup_folder",
    type=Path,
    required=True,
    help="Path to backup folder on external USB drive",
)
@click.option(
    "-d",
    "--delete",
    is_flag=True,
    default=False,
    help="Delete backed up files not in the sequence folder (use with caution)",
    required=False,
)
def backup(seq_folder: Path, backup_folder: Path, delete: bool = False) -> None:
    """
    Backup all sequence data files to a local USB drive.

    """
    # Set up child log
    log = logging.getLogger("backup")
    log.info(divider)
    log.debug(identify_cli_command())
    log.info(f"Backing up sequence data from {seq_folder} to {backup_folder}")

    selective_rsync(
        source_dir=seq_folder,
        target_dir=backup_folder,
        recursive=True,
        delete=delete,
    )
    log.info(divider)
