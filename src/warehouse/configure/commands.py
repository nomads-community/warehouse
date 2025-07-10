import logging
from pathlib import Path

import click
import yaml

from warehouse.configure.configure import select_int_from_list
from warehouse.lib.exceptions import PathError
from warehouse.lib.general import check_path_present, identify_path_by_search
from warehouse.lib.logging import divider, identify_cli_command
from warehouse.lib.regex import Regex_patterns

script_dir = Path(__file__).parent.resolve()


@click.command(
    short_help="Configure warehouse with default files, locations and other variables"
)
@click.option(
    "-d",
    "--google_drive_data_folder",
    type=Path,
    required=True,
    help="Shared data folder synchronised to Google Drive",
)
@click.option(
    "-n",
    "--name_group",
    type=str,
    required=True,
    help="Name of group e.g. UCB",
)
@click.option(
    "-r",
    "--raw_sequence_folder",
    type=Path,
    required=True,
    help="Path to folder containing all raw sequencing data stored on local sequencing machine",
)
@click.option(
    "-g",
    "--git_folder",
    type=Path,
    required=False,
    default=Path.home() / "git",
    help="Path to git folder containing nomadic and savanna clones. Default is ~/git",
)
def configure(
    name_group: str,
    raw_sequence_folder: Path,
    google_drive_data_folder: Path,
    git_folder: Path,
) -> None:
    """
    Setup warehouse with default file locations that are stored in a yml file for running other commands

    """
    # Set up child log
    log = logging.getLogger(script_dir.stem)
    log.info(divider)
    log.debug(identify_cli_command())

    config_file = script_dir / "warehouse_config.yml"

    config_data = {}
    # Identify and add the shared drive folders
    for target in ["experimental", "sequence"]:
        path = google_drive_data_folder / target
        check_path_present(path)
        config_data[target] = str(path.resolve())
    # Add the templates folder
    template_path = google_drive_data_folder / "experimental" / "templates"
    config_data["templates"] = str(template_path.resolve())

    # Find possible sample metadata files
    log.info("Searching for possible metadata files")
    sample_folder_path = google_drive_data_folder / "sample"
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
    config_data["metadata"] = str(metadata_file.resolve())

    config_data["git_folder"] = str(git_folder.resolve())

    # Check the group name is valid:
    group_details_yaml = script_dir.parent / "templates" / "group_details.yml"
    with open(group_details_yaml, "r") as f:
        groups = yaml.safe_load(f)
    if name_group not in groups.keys():
        raise PathError(
            f"{name_group} not found in known groups: {list(groups.keys())}"
        )
    config_data["group_name"] = name_group

    # raw sequence data folder
    check_path_present(raw_sequence_folder)
    config_data["raw_sequence_folder"] = str(raw_sequence_folder.resolve())

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
