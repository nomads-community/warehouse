import click
from pathlib import Path
from collections import OrderedDict
import logging

from warehouse.lib.logging import config_root_logger, identify_cli_command, divider
from warehouse.metadata.commands import metadata
from warehouse.seqfolders.commands import seqfolders
from warehouse.visualise.commands import visualise
from warehouse.extract.commands import extract

# ================================================================
# Entry point for all sub-commands
#
# ================================================================

# Configure logging before subcommand execution
warehouse_dir = Path(__file__).parent.parent.parent.resolve()
log_dir = warehouse_dir / "logs"
config_root_logger(log_dir=log_dir, verbose=False)

class OrderedGroup(click.Group):
    def __init__(self, name=None, commands=None, **attrs):
        super(OrderedGroup, self).__init__(name, commands, **attrs)
        #: the registered subcommands by their exported names.
        self.commands = commands or OrderedDict()

    def list_commands(self, ctx):
        return self.commands


@click.group(cls=OrderedGroup)
@click.version_option(message="%(prog)s-v%(version)s")
def cli():
    """
    Standardisation, processing and sorting of NOMADS experimental, sample and sequence data

    """
    pass


# ================================================================
# Individual sub-commands
# ================================================================

cli.add_command(metadata)
cli.add_command(seqfolders)
cli.add_command(visualise)
cli.add_command(extract)

if __name__ == "__main__":
    cli()
