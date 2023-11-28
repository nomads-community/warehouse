import click
import re
from extract.extract import ExtractMetadata

id_regex = r'^[A-Z]{4}\d{3}$'

@click.command(short_help="Extract metadata tables from Excel experimental worksheets ")
@click.option(
    "-d",
    "--data_folder",
    type=str,
    required=True,
    help="Path to folder containing Excel experimental worksheets."
)

@click.option(
    "-x",
    "--export_folder",
    type=str,
    required=True,
    help="Path to export csv files to."
)

@click.option(
    "-e",
    "--expt_id",
    type=str,
    required=False,
    default = "",
    help="Experiment ID. For example SLMM005.",
    callback=lambda ctx, param, value: validate_id(value) 
)

def extract(data_folder, expt_id, export_folder):
    """
    Extract relevent metadata from Excel spreadsheet(s) 
    """
    #Extract metadata
    ExtractMetadata(data_folder, export_folder, expt_id)


def validate_id(expt_id):
    if not re.match(id_regex, expt_id):
        raise click.BadParameter(f'ID must match format {id_regex}')
    return expt_id
