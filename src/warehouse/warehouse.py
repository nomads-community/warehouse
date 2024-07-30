import click
from warehouse.metadata.commands import metadata
from warehouse.seqfolders.commands import seqfolders
from warehouse.visualise.commands import visualise

# ================================================================
# Entry point for all sub-commands
#
# ================================================================


@click.group()
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
