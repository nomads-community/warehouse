import logging
from pathlib import Path

import click

from warehouse.configure.configure import get_configuration_value
from warehouse.lib.logging import divider, identify_cli_command
from warehouse.lib.synchronise import move_folder

script_dir = Path(__file__).parent.resolve()


@click.command(short_help="Backup sequence data folder to a local hard disk drive")
@click.option(
    "-b",
    "--backup_folder",
    type=Path,
    required=True,
    help="Path to backup folder on external USB drive",
)
def backup(backup_folder: Path) -> None:
    """
    Backup all sequence data files to a local USB drive.

    """
    # Read in from configuration if not supplied
    seq_folder = get_configuration_value("sequence_folder")

    # Set up child log
    log = logging.getLogger(script_dir.stem)
    log.info(divider)
    log.debug(identify_cli_command())

    log.info(f"Backing up sequence data from {seq_folder} to {backup_folder}")
    move_folder(source_path=seq_folder, dest_path=backup_folder, as_sudo=True)

    log.info(divider)
