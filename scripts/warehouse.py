import click
from metadata.commands import metadata
from nomadic.commands import nomadic
from extract.commands import extract

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
cli.add_command(extract)


if __name__ == "__main__":
    cli()
