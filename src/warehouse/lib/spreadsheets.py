import logging

from openpyxl.utils import range_boundaries
from openpyxl.worksheet.datavalidation import DataValidation

# Get logging process
log = logging.getLogger("spreadsheets")


def apply_worksheet_validation_rule(worksheet, validation_dict: dict) -> None:
    """
    Restores spreadsheet data validation rules from a dictionary

    worksheet: openpyxl workbook/sheet
    validation_dict: dictionary containing data validation rules

    """
    # Define validation refs
    ref_type = validation_dict.get("ref_type")
    ref_range = validation_dict.get("ref_range")

    # Determine which cell or cells it should be applied to
    cell_range = validation_dict.get("apply_to_cell")

    log.debug(
        f"         Applying {ref_type} with lookup range {ref_range} to range {cell_range}"
    )

    # Range of cells
    if ":" in cell_range:
        min_col, min_row, max_col, max_row = range_boundaries(cell_range)

        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                each_cell = worksheet.cell(row=row, column=col)
                data_validation = DataValidation(type=ref_type, formula1=ref_range)
                worksheet.add_data_validation(data_validation)
                data_validation.add(each_cell)
    # Single cell
    else:
        data_validation = DataValidation(type=ref_type, formula1=ref_range)
        worksheet.add_data_validation(data_validation)
        data_validation.add(worksheet[cell_range])
