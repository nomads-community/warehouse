import logging
from pathlib import Path

import click

from warehouse.aggregate.aggregate import aggregate, currently_sequencing
from warehouse.configure.configure import get_configuration_value
from warehouse.extract.extract import extract
from warehouse.lib.general import produce_dir
from warehouse.lib.logging import divider, identify_cli_command, minor_header
from warehouse.metadata.metadata import ExpDataMerge, metadata
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
    if full_config:
        seq_data_folder = get_configuration_value("sequence_folder")

    ######################################################
    # Rebuild templates
    templates(group_name=group_name, output_folder=shared_templates_dir)

    ######################################################
    # Pull in experimental data
    minor_header(log, "Experimental data:")
    exp_data = ExpDataMerge(Path(shared_exp_dir), output_folder, verbose=verbose)

    ######################################################
    # Run all the full_config processes before running metadata to ensure everything is
    # in its correct place
    if full_config:
        ######################################################
        # Build sequence data folders
        # TODO: Add logic for if this is the first time being run
        seqfolders(exp_data, seq_data_folder)

        ######################################################
        # Aggregate data into one location
        if not currently_sequencing():
            aggregate(seq_data_folder, git_dir)
        else:
            log.info("Skipping aggregation as a run is currently in progress")
            log.info(divider)

        ######################################################
        # Selectively extract to cloud share
        extract(seq_folder=seq_data_folder, output_folder=shared_seq_dir)

    ######################################################
    # Pull in experimental data
    seq_data, sample_data, combined_data = metadata(
        exp_data=exp_data,
        seq_folder=shared_seq_dir,
        sample_metadata_file=shared_sample_file,
        output_folder=output_folder,
    )

    ######################################################
    # View dashboard
    visualise(
        exp_data=exp_data,
        seq_data=seq_data,
        sample_data=sample_data,
        combined_data=combined_data,
    )
