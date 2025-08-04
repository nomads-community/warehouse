import logging
from pathlib import Path

import yaml
from openpyxl import load_workbook

from warehouse.lib.exceptions import DataFormatError
from warehouse.lib.general import identify_path_by_search, pad_list, produce_dir
from warehouse.lib.logging import divider, major_header
from warehouse.lib.regex import Regex_patterns
from warehouse.lib.spreadsheets import (
    apply_worksheet_conditional_formatting,
    apply_worksheet_validation_rule,
)

# Resolve file / folder locations irrespective of cwd
script_dir = Path(__file__).parent.resolve()
templates_dir = script_dir.parent.parent.parent / "templates"


def templates(group_name: str, output_folder: Path):
    """
    Update NOMADS templates with user and project names
    """

    # Set up child log
    log = logging.getLogger(script_dir.stem)
    major_header(log, "Generating templates:")

    # Load group details from YAML file
    group_details_yaml = script_dir / "group_details.yml"
    with open(group_details_yaml, "r") as f:
        details = yaml.safe_load(f)

    # Load data validation details from YAML file
    data_validations_yaml = script_dir / "data_validations.yml"
    with open(data_validations_yaml, "r") as f:
        validations = yaml.safe_load(f)

    # Load conditional formatting details from YAML file
    conditional_formatting_yaml = script_dir / "conditional_formatting.yml"
    with open(conditional_formatting_yaml, "r") as f:
        formatting_rules = yaml.safe_load(f)

    # Extract group names
    grp_details = details.get(group_name)
    if grp_details is None:
        raise DataFormatError(
            f"-g '{group_name}' not found. Options are {list(details.keys())}."
        )

    if not output_folder:
        log.info("You have not defined an output folder (-o) option")
        log.info(divider)
        return

    # Identify all template files
    template_fns = identify_path_by_search(
        folder_path=templates_dir, pattern=Regex_patterns.EXCEL_FILE, files_only=True
    )
    # Limit to those relevent to the group:
    template_fns = [t for t in template_fns if t.stem in grp_details.get("templates")]

    # Create the output folder
    produce_dir(output_folder)

    # For each template change the names, initials and projects
    for template_fn in template_fns:
        # Load the workbook
        workbook = load_workbook(template_fn)
        # Select the correct worksheet
        worksheet = workbook["Reference"]

        # Names, initials and projects are in cols I,J and L
        for dict_key, col_num in zip(grp_details.keys(), [9, 10, 12]):
            # Extract the correct values to enter
            details = pad_list(grp_details, dict_key, 10)
            # Names, initials and projects are in rows 17 to 26
            for count, xl_row in enumerate(range(17, 27)):
                # Define the cell to edit
                cell = worksheet.cell(row=xl_row, column=col_num)
                # Assign the new value to the cell
                cell.value = details[count]

        # Then restore the data validation logic that is somehow overwritten when replacing the above details
        log.debug(f"{template_fn.stem}")

        for sheetname, validation in validations.get(template_fn.stem, {}).items():
            # Load worksheet
            worksheet = workbook[sheetname]
            log.debug(type(worksheet))
            log.debug(f"   Worksheet name: {sheetname}")
            for validationname, validation in validation.items():
                log.debug(f"      Validation name: {validationname}")
                apply_worksheet_validation_rule(worksheet, validation)

        # Then restore the conditional formatting logic that is somehow overwritten when replacing the above details
        for sheetname, format in formatting_rules.get(template_fn.stem, {}).items():
            # Load worksheet
            worksheet = workbook[sheetname]
            log.debug(type(worksheet))
            log.debug(f"   Worksheet name: {sheetname}")
            for formattingnname, format in format.items():
                log.debug(f"      Formatting name: {formattingnname}")
                apply_worksheet_conditional_formatting(worksheet, format)

        # Define output path
        output_path = Path(output_folder) / template_fn.name
        log.info(f"{template_fn.name} output to {output_folder}")
        # Save the modified workbook
        workbook.save(output_path)
