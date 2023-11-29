import click
from extract.extract import ExtractMetadata


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
)

def extract(data_folder, expt_id, export_folder):
    """
    Extract relevent metadata from Excel spreadsheet(s) 
    """
    #Extract metadata
    ExtractMetadata(data_folder, export_folder, expt_id)
