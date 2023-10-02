import click
from metadata.commands import metadata
from nomadic.commands import nomadic

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


if __name__ == "__main__":
    cli()
