import logging
from pathlib import Path

import click

from warehouse.aggregate.aggregate import aggregate, currently_sequencing
from warehouse.configure.configure import get_configuration_value
from warehouse.extract.extract import extract
from warehouse.lib.general import produce_dir
from warehouse.lib.logging import divider, identify_cli_command
from warehouse.metadata.metadata import metadata
from warehouse.seqfolders.seqfolders import seqfolders
from warehouse.templates.templates import templates
from warehouse.visualise.commands import visualise

script_dir = Path(__file__).parent.resolve()


@click.command(short_help="Process all NOMADS experimental, sample and sequence data")
@click.pass_context
def process(ctx):
    """
    Validate, merge and export experimental, sample and sequence data
    """

    # Set up child log and enter cli cmd
    log = logging.getLogger(script_dir.stem + "_commands")
    log.debug(identify_cli_command())
    # Define whether output should be verbose
    verbose = ctx.obj.get("VERBOSE", False)

    ######################################################
    # pull in warehouse configure definitions
    full_config = get_configuration_value("full_config")
    shared_exp_dir = get_configuration_value("shared_experimental_dir")
    shared_seq_dir = get_configuration_value("shared_sequence_dir")
    shared_templates_dir = get_configuration_value("shared_templates_dir")
    shared_sample_file = get_configuration_value("shared_sample_file")
    git_dir = get_configuration_value("git_dir")
    group_name = get_configuration_value("group_name")
    output_folder = get_configuration_value("output_folder")
    produce_dir(output_folder)

    ######################################################
    log.info(divider)
    log.info("Generating templates")
    log.info(divider)
    templates(group_name=group_name, output_folder=shared_templates_dir)

    ######################################################
    log.info(divider)
    log.info("Loading experimental data")
    log.info(divider)
    exp_data, seq_data, sample_data, combined_data = metadata(
        exp_folder=shared_exp_dir,
        seq_folder=shared_seq_dir,
        sample_metadata_file=shared_sample_file,
        output_folder=output_folder,
        verbose=verbose,
    )

    ######################################################
    if full_config:
        seq_data_folder = get_configuration_value("sequence_folder")
        log.info(divider)
        log.info("Creating sequence folders as required")
        log.info(divider)
        # Ensure all seqfolders have been created
        seqfolders(exp_data, seq_data_folder)

    ######################################################
    # Need to ensure that aggregate is not run while a run is happening
    if full_config and not currently_sequencing():
        log.info(divider)
        log.info("Aggregating sequence data into sequence folders")
        log.info(divider)
        aggregate(seq_data_folder, git_dir)

    ######################################################
    if full_config:
        log.info(divider)
        log.info("Extracting sequence data summaries to shared cloud folder")
        log.info(divider)
        extract(seq_folder=seq_data_folder, output_folder=shared_seq_dir)

    ######################################################

    visualise(
        exp_data=exp_data,
        seq_data=seq_data,
        sample_data=sample_data,
        combined_data=combined_data,
    )
