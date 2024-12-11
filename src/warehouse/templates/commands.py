import logging
from pathlib import Path

import click
import yaml
from openpyxl import load_workbook
from openpyxl.worksheet.datavalidation import DataValidation

from warehouse.lib.exceptions import DataFormatError
from warehouse.lib.general import identify_files_by_search, produce_dir
from warehouse.lib.logging import divider, identify_cli_command
from warehouse.lib.regex import Regex_patterns

script_dir = Path(__file__).parent.resolve()


@click.command(short_help="Update template files with group specific data")
@click.option(
    "-o",
    "--output_folder",
    type=Path,
    required=True,
    help="Path to folder where the updated templates should be output to",
)
@click.option(
    "-g",
    "--group_name",
    type=str,
    required=True,
    help="Name of group to use",
)
def templates(group_name: str, output_folder: Path):
    """
    Update templates with user and project names
    """

    # Set up child log
    log = logging.getLogger("templates_commands")
    log.info(divider)
    log.debug(identify_cli_command())

    # Identify and load targets dict from YAML file
    yaml_file = script_dir / "group_details.yaml"
    with open(yaml_file, "r") as f:
        details = yaml.safe_load(f)

    # Extract group names
    grp_details = details.get(group_name)
    if grp_details is None:
        raise DataFormatError(
            f"Group '{group_name}' not found. Options are {list(details.keys())}."
        )

    # Identify all template files
    templates_dir = Path.cwd() / "templates"
    template_fns = identify_files_by_search(templates_dir, Regex_patterns.EXCEL_FILE)

    # Create the output folder
    produce_dir(output_folder)

    # For each template change the names, initials and projects
    for template_fn in template_fns:
        # Load the workbook
        workbook = load_workbook(template_fn)
        # Select the correct worksheet
        worksheet = workbook["reference"]

        for dict_key, col_num in zip(grp_details.keys(), [9, 10, 12]):
            # Extract the correct values to enter
            details = pad_list(grp_details, dict_key, 6)
            # Names are in I3-I8, Initials in J3 to J8 and Projects in L3 to L8
            for count, xl_row in enumerate(range(3, 8)):
                # Define the cell to edit
                cell = worksheet.cell(row=xl_row, column=col_num)
                # Assign the new value to the cell
                cell.value = details[count]

        # Above removes the dropdown references on the assay sheet so reinsert
        worksheet = workbook["Assay"]
        # Create UserName Validation
        data_validation = DataValidation(type="list", formula1="Reference!I3:I8")
        # Add the DataValidation to correct cell
        worksheet.add_data_validation(data_validation)
        data_validation.add(worksheet["C3"])

        # Create Project validation
        data_validation = DataValidation(type="list", formula1="Reference!L3:L8")
        # Add the DataValidation to correct cell
        worksheet.add_data_validation(data_validation)
        data_validation.add(worksheet["C7"])

        # Define output path
        output_path = output_folder / template_fn.name
        # Save the modified workbook
        workbook.save(output_path)

    log.info(divider)


def pad_list(dictionary: dict, key: str, padlength: int) -> list:
    details = dictionary.get(key)
    details = details + [""] * (padlength - len(details))
    return details
