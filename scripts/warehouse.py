import click
from metadata.commands import metadata
from seqfolders.commands import seqfolders
from visualise.commands import visualise

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
