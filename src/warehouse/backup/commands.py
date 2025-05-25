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
    help="Path to folder containing all sequencing data",
)
@click.option(
    "-b",
    "--backup_folder",
    type=Path,
    required=True,
    help="Path to backup folder on local hard disk drive",
)
def backup(seq_folder: Path, backup_folder: Path):
    """
    Backup all sequence data files to a local hard disk drive.

    """
    # Set up child log
    log = logging.getLogger("backup")
    log.info(divider)
    log.debug(identify_cli_command())

    selective_rsync(seq_folder, backup_folder, exclusions=None, recursive=True)
    log.info(divider)
