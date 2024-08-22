import click
from collections import OrderedDict
from warehouse.metadata.commands import metadata
from warehouse.seqfolders.commands import seqfolders
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
def cli():
    """
    NOMADS Sequencing Data - experimental outputs

    """
    pass


# ================================================================
# Individual sub-commands
# ================================================================

cli.add_command(metadata)
cli.add_command(seqfolders)
cli.add_command(visualise)

if __name__ == "__main__":
    cli()
