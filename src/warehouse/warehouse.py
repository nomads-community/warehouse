from collections import OrderedDict
from pathlib import Path

import click

from warehouse.aggregate.commands import aggregate
from warehouse.extract.commands import extract
from warehouse.lib.logging import config_root_logger
from warehouse.metadata.commands import metadata
from warehouse.seqfolders.commands import seqfolders
from warehouse.templates.commands import templates
from warehouse.visualise.commands import visualise

# ================================================================
# Entry point for all sub-commands
#
# ================================================================


class OrderedGroup(click.Group):
    def __init__(self, name=None, commands=None, **attrs):
        super(OrderedGroup, self).__init__(name, commands, **attrs)
        #: the registered subcommands by their exported names.
        self.commands = commands or OrderedDict()

    def list_commands(self, ctx):
        return self.commands


@click.group(cls=OrderedGroup)
@click.version_option(message="%(prog)s-v%(version)s")
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose logging.",
)
@click.pass_context
def cli(ctx, verbose):
    """
    Standardisation, extraction and visualisation of NOMADS experimental and sequencing data

    """
    # Configure logging before subcommand execution
    warehouse_dir = Path(__file__).parent.parent.parent.resolve()
    log_dir = warehouse_dir / "logs"
    config_root_logger(log_dir=log_dir, verbose=verbose)


# ================================================================
# Individual sub-commands
# ================================================================

cli.add_command(templates)
cli.add_command(metadata)
cli.add_command(seqfolders)
cli.add_command(aggregate)
cli.add_command(extract)
cli.add_command(visualise)

if __name__ == "__main__":
    cli()
