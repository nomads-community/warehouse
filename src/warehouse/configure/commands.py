import logging
import sys
from pathlib import Path

import click
import yaml

from warehouse.configure.configure import select_int_from_list
from warehouse.lib.exceptions import PathError
from warehouse.lib.general import (
    check_path_present,
    identify_path_by_search,
)
from warehouse.lib.logging import divider, identify_cli_command
from warehouse.lib.regex import Regex_patterns

script_dir = Path(__file__).parent.resolve()


@click.command(short_help="Configure default files and variables")
@click.option(
    "-d",
    "--shared_data_folder",
    type=Path,
    required=True,
    help="Shared data folder synchronised to Google Drive",
)
@click.option(
    "-n",
    "--nomadic_folder",
    default=Path.home() / "git" / "nomadic",
    type=Path,
    help="Path to nomadic workspace [default: ~/git/nomadic]",
)
@click.option(
    "-v",
    "--savanna_folder",
    default=Path.home() / "git" / "savanna" / "results",
    type=Path,
    help="Path to savanna folder [default: ~/git/savanna/results]",
)
@click.option(
    "-s",
    "--sequence_folder",
    type=Path,
    help="Path to folder containing all raw sequencing data. Only needed if this is a sequencing laptop",
)
def configure(
    sequence_folder: Path,
    nomadic_folder: Path,
    savanna_folder: Path,
    shared_data_folder: Path,
) -> None:
    """
    Configure all variables necessary to routinely run warehouse. Values are checked and then stored
    in a yml file for other commands to utilise so user doesn't have to re-enter them each
    time.

    """
    # Set up child log
    log = logging.getLogger(script_dir.stem + "_commands")
    log.debug(identify_cli_command())

    # Store variables in a dictionary
    config_data = {}

    # Check if sequence folder supplied
    if sequence_folder and not sys.platform == "win32":
        # Add sequence folder
        check_path_present(sequence_folder)
        config_data["full_config"] = True
        config_data["sequence_folder"] = str(sequence_folder.resolve())
    else:
        config_data["full_config"] = False

    # Identify experimental folder
    exp_path = shared_data_folder / "experimental"
    check_path_present(exp_path, raise_error=True)
    config_data["shared_experimental_dir"] = str(exp_path.resolve())
    # Add the templates folder
    template_path = exp_path / "templates"
    config_data["shared_templates_dir"] = str(template_path.resolve())
    # Identify sequence folder
    path = shared_data_folder / "sequence"
    check_path_present(path, raise_error=True)
    config_data["shared_sequence_dir"] = str(path.resolve())

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
    config_data["shared_sample_file_config"] = str(
        metadata_file.with_suffix(".yml").resolve()
    )

    # Check group details yaml exists and load
    group_details_yaml = template_path / "group_details.yml"
    check_path_present(group_details_yaml, isfile=True, raise_error=True)
    with open(group_details_yaml, "r") as f:
        details = yaml.safe_load(f)
    config_data["group_name"] = details.get("group", "default")
    config_data["names"] = details.get("names", [])
    config_data["projects"] = details.get("projects", [])
    config_data["templates"] = details.get("templates", [])

    # Identify and load targets dict from YAML file
    locations_yaml = script_dir.parent / "aggregate" / "locations.yml"
    with open(locations_yaml, "r") as f:
        locations = yaml.safe_load(f)
    # Add in the minknow dir
    config_data["minknow_dir"] = "/var/lib/minknow/data"

    # Add nomadic folder
    check_path_present(nomadic_folder, raise_error=True)
    config_data["nomadic_dir"] = str(nomadic_folder.resolve())

    # Add savanna folder
    config_data["savanna_dir"] = str(savanna_folder.resolve())

    # Define the output folder
    output_folder = (
        script_dir.parent.parent.parent
        / "notebooks"
        / "data"
        / details.get("group", "default")
        / metadata_file.stem
    )
    config_data["output_folder"] = str(output_folder.resolve())

    # Give user feedback
    log.info("Identified the following entries:")
    for key, value in config_data.items():
        log.info(f"   {key}: {value}")
    # Write the configuration to the YAML file
    config_file = script_dir / "warehouse_config.yml"
    try:
        with open(config_file, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        log.info(f"Configuration successfully written to {config_file}")
    except IOError as e:
        log.error(f"Error writing YAML file {config_file}: {e}")
    log.info(divider)
