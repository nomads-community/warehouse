import logging
import sys
from pathlib import Path

import click
import yaml

from warehouse.configure.configure import select_int_from_list
from warehouse.lib.exceptions import GenError, PathError
from warehouse.lib.general import check_path_present, identify_path_by_search
from warehouse.lib.logging import divider, identify_cli_command
from warehouse.lib.regex import Regex_patterns

script_dir = Path(__file__).parent.resolve()


@click.command(short_help="Configure default files and variables")
@click.option(
    "-d",
    "--shared_data_folder",
    type=Path,
    help="Shared data folder synchronised to Google Drive",
)
@click.option(
    "-n",
    "--name_group",
    type=str,
    help="Name of group e.g. UCB",
)
@click.option(
    "-s",
    "--sequence_folder",
    type=Path,
    help="Path to folder containing all raw sequencing data stored on local sequencing machine",
)
@click.option(
    "-g",
    "--git_folder",
    type=Path,
    default=Path.home() / "git",
    help="Path to git folder containing nomadic and savanna clones. Default is ~/git",
)
@click.option(
    "-l",
    "--list_groups",
    is_flag=True,
    default=False,
    help="List all groups available to select from",
)
def configure(
    name_group: str,
    sequence_folder: Path,
    shared_data_folder: Path,
    git_folder: Path,
    list_groups: bool,
) -> None:
    """
    Setup warehouse with default file locations that are stored in a yml file for running other commands

    """
    # Set up child log
    log = logging.getLogger(script_dir.stem + "_commands")
    log.info(divider)
    log.debug(identify_cli_command())

    # Load group details from YAML file
    group_details_yaml = script_dir.parent / "templates" / "group_details.yml"
    with open(group_details_yaml, "r") as f:
        groups = yaml.safe_load(f)
    # List group options
    if list_groups:
        groups = ", ".join(list(groups.keys()))
        log.info(f"Available groups are: {groups}")
        log.info(divider)
        return

    # Check correct args passed
    if not shared_data_folder:
        log.info("Please enter your shared data folder path with the -d flag")
        log.info(divider)
        return
    if not name_group:
        log.info("Please enter your -n group name (use -l to list groups)")
        log.info(divider)
        return

    config_file = script_dir / "warehouse_config.yml"
    config_data = {}

    # Check if sequence folder supplied
    if sequence_folder and not sys.platform == "win32":
        # Add sequence folder
        check_path_present(sequence_folder)
        config_data["full_config"] = True
        config_data["sequence_folder"] = str(sequence_folder.resolve())
    else:
        config_data["full_config"] = False

    # Identify and add the shared drive folders
    for target in ["experimental", "sequence"]:
        path = shared_data_folder / target
        check_path_present(path, raise_error=True)
        config_data[f"shared_{target}_dir"] = str(path.resolve())
    # Add the templates folder
    template_path = shared_data_folder / "experimental" / "templates"
    config_data["shared_templates_dir"] = str(template_path.resolve())

    # Find possible sample metadata files
    log.info("Searching for possible sample metadata files")
    sample_folder_path = shared_data_folder / "sample"
    check_path_present(sample_folder_path, raise_error=True)
    metadata_potentials = identify_path_by_search(
        folder_path=sample_folder_path,
        pattern=Regex_patterns.EXCEL_CSV_FILE,
        recursive=True,
        files_only=True,
    )
    # Check each path for a corresponding yml file
    metadata_paths = []
    for mp in metadata_potentials:
        yml_file = mp.with_suffix(".yml")
        if yml_file.exists():
            metadata_paths.append(mp)
    if not metadata_paths:
        raise PathError(f"No metadata files found in {sample_folder_path} ")
    if len(metadata_paths) > 1:
        path_names = [p.name for p in metadata_paths]
        i = select_int_from_list(path_names)
        metadata_file = metadata_paths[i]
    else:
        metadata_file = metadata_paths[0]
    config_data["shared_sample_file"] = str(metadata_file.resolve())

    # Add in git folder
    config_data["git_dir"] = str(git_folder.resolve())

    # Check the group name is valid:
    if name_group not in groups.keys():
        raise GenError(f"{name_group} not found in known groups: {list(groups.keys())}")
    config_data["group_name"] = name_group

    # Define the output folder
    output_folder = (
        script_dir.parent.parent.parent
        / "notebooks"
        / "data"
        / name_group
        / metadata_file.stem
    )
    config_data["output_folder"] = str(output_folder.resolve())

    # Give user feedback
    log.info("Identified the following entries:")
    for key, value in config_data.items():
        log.info(f"   {key}: {value}")
    # Write the configuration to the YAML file
    try:
        with open(config_file, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        log.info(f"Configuration successfully written to {config_file}")
    except IOError as e:
        log.error(f"Error writing YAML file {config_file}: {e}")
    log.info(divider)
