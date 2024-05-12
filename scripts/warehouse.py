import click
from metadata.commands import metadata
from nomadic.commands import nomadic
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
cli.add_command(nomadic)
cli.add_command(visualise)


if __name__ == "__main__":
    cli()
