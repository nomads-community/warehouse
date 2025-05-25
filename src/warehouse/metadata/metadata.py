import logging
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pretty_errors

from warehouse.lib.dataframes import (
    collapse_repeat_columns,
    concat_files_add_expID,
    identify_duplicate_colnames,
    identify_export_dataframe_attributes,
    merge_additional_rxn_level_fields,
)
from warehouse.lib.decorators import singleton
from warehouse.lib.dictionaries import (
    create_dict_from_ini,
    filter_dict_by_key_or_value,
    filter_nested_dict,
    get_nested_key_value,
    reformat_nested_dict,
)
from warehouse.lib.exceptions import DataFormatError
from warehouse.lib.general import (
    identify_exptid_from_path,
    identify_files_by_search,
    produce_dir,
)
from warehouse.lib.logging import divider
from warehouse.lib.regex import Regex_patterns

pretty_errors.configure(stack_depth=1, display_locals=1)

# Define logging process
log = logging.getLogger("metadata")

# Define where the script is running from so you can reference internal files etc
script_dir = Path(__file__).parent.resolve()
default_ini_folder = Path(script_dir, "dataschemas/")


@singleton
class ExpDataSchemaFields:
    """
    Pull in all of the dataschema fields that are in separate ini files
    """

    def __init__(self):
        # Find all .ini files
        ini_files = identify_files_by_search(
            default_ini_folder, re.compile("exp_.*.ini"), False, False
        )
        # Separate into the two types
        common_ini = [path for path in ini_files if "common" in path.name]
        other_inis = [path for path in ini_files if "common" not in path.name]

        # Pull in the common fields into the dataschema dict
        common_fields_dict = create_dict_from_ini(common_ini)
        dataschema_dict = common_fields_dict.copy()

        for ini_file in other_inis:
            # Identify the experiment type from filename:
            expt_type = ini_file.name.replace(".ini", "").replace("exp_", "")

            # Create additional entries that could be created during merging operations.
            # There are a number of fields that are common to all experimental templates e.g. EXPT_ID
            # When df are merged these will be given the expt_type suffixe e.g. sWGA
            # However the original df will not have these suffixes
            # Therefore for the common fields, add in new ref keys, as well as field and labels
            # - the reference field e.g. EXP_ID_SWGA (key)
            # - the suffixed field name e.g. exp_id_sWGA (field)
            # - the human readable label e.g. Experiment ID (label)
            # Note that this will create all possible combinations, but not necessarily the correct ones
            modified_dict = {}
            for key, entry in common_fields_dict.items():
                new_key = f"{key}_{expt_type.upper()}"
                new_entry = {"field": entry["field"] + "_" + expt_type}
                modified_dict[new_key] = entry | new_entry
            # Add suffixed fields to the dataschema
            dataschema_dict.update(modified_dict)

            # Pull in assay specific fields from ini file and add to dataschema and as a attribute
            libdict = create_dict_from_ini(ini_file)
            dataschema_dict.update(libdict)
            libname = f"{expt_type}_field_labels"
            setattr(self, libname, libdict)

        # Create dataschema_dict attribute
        self.dataschema_dict = dataschema_dict

        # Set attributes for each of the entries in the dataschema
        for dict_key in self.dataschema_dict.keys():
            field_value = get_nested_key_value(self.dataschema_dict, dict_key, "field")
            label_value = get_nested_key_value(self.dataschema_dict, dict_key, "label")
            setattr(self, dict_key.upper(), (field_value, label_value))


class ExpMetadataParser:
    """
    Parse and validate the experimental and individual rxn metadata from an individual Excel spreadsheet.

    """

    def __init__(
        self,
        file_path: Path,
        output_folder: Path = None,
        include_unclassified: bool = False,
    ):
        """
        Load and sanity check the metadata

        """
        # Pull in the dynamically created ExpDataSchema
        ExpDataSchema = ExpDataSchemaFields()

        log.info(f"{file_path.name}")
        self.tabnames = ["expt_metadata", "rxn_metadata"]
        # Store filename
        self.filepath = file_path

        # Extract sheetnames
        sheets = pd.ExcelFile(file_path).sheet_names
        # Check both sheets / tabs are present
        if not (self.tabnames[0] in sheets and self.tabnames[1] in sheets):
            raise DataFormatError(f"Missing tabs in {file_path}")

        # Load expt data
        ###################
        self.expt_df = self._extract_excel_data(file_path, self.tabnames[0])
        self.expt_id = self.expt_df[ExpDataSchema.EXP_ID[0]].iloc[0]
        self.expt_date = self.expt_df[ExpDataSchema.EXP_DATE[0]].iloc[0]
        self._check_valid_date_format(self.expt_date)
        self.expt_summary = self.expt_df[ExpDataSchema.EXP_SUMMARY[0]].iloc[0]
        self.expt_type = self.expt_df[ExpDataSchema.EXP_TYPE[0]].iloc[0]
        # Save the number of samples entered into the assay tab
        num_rxn = self.expt_df[ExpDataSchema.EXP_RXNS[0]].iloc[0]
        # Check validity of expt data
        ###################
        self._define_expt_variables()
        self._check_for_columns(self.expt_req_cols, self.expt_df)
        self._check_number_rows(1, self.expt_df, self.filepath)
        self._check_expt_id_fn_sheet()
        log.info("      Experimental metadata passed formatting checks.")

        # Load rxn data
        ###################
        self.rxn_df = self._extract_excel_data(file_path, self.tabnames[1])
        # Check validity of rxn data
        ###################
        self._check_for_columns(self.rxn_req_cols, self.rxn_df)
        self.rxn_rows = self._check_number_rows(num_rxn, self.rxn_df, self.filepath)
        self._check_entries_unique(self.rxn_unique_cols, self.rxn_df)
        self._check_entries_not_blank(self.rxn_notblank_cols, self.rxn_df)
        if len(self.barcode_pattern) > 0:
            self.barcodes = self.rxn_df[ExpDataSchema.BARCODE[0]].tolist()
            if include_unclassified:
                self.barcodes.append("unclassified")
            self._check_barcodes_valid()
        log.info("      Rxn metadata passed formatting checks.")

        log.info(f"      Merging experimental and rxn data for {self.expt_id}...")
        self.df = pd.merge(self.expt_df, self.rxn_df, on="expt_id", how="inner")
        # Add expt_type back into the rxn dataframe after the merge otherwise there
        # will be duplicate expt_type cols
        self.rxn_df[ExpDataSchema.EXP_TYPE[0]] = self.rxn_df.get(
            ExpDataSchema.EXP_TYPE[0], self.expt_type
        )

        if output_folder:
            # Store individual experiments in a subfolder
            individual_dir = output_folder / "individual_expts"
            produce_dir(individual_dir)
            log.info(
                f"      Outputting experimental data to folder: {individual_dir.name}"
            )
            output_dict = {"expt": self.expt_df, "rxn": self.rxn_df}
            for output in output_dict:
                filename = self.expt_id + "_" + output + "_metadata.csv"
                path = individual_dir / filename
                output_dict[output].to_csv(path, index=False)
        log.info("Done")

    def _extract_excel_data(self, filename: Path, tabname: str) -> pd.DataFrame:
        """
        Extract data from valid Excel sheets and return a dataframe.

        Args:
            filename(Path): Path object to file
            tabname(str): Excel tab in sheet

        Returns:
            dataframe: Data from Excel tab
        """

        # Extract data and drop empty rows
        data = pd.read_excel(filename, sheet_name=tabname)
        data.dropna(how="all", inplace=True)

        return data

    def _define_expt_variables(self) -> None:
        """
        Define all required fields, counts etc for the exp type.

        """
        log.info(f"      Identified as {self.expt_type} type experiment")
        self.rxn_identifier_col = self.expt_type + "_identifier"
        ExpDataSchema = ExpDataSchemaFields()

        if self.expt_type == "seqlib":
            self.expt_req_cols = [ExpDataSchema.EXP_ID[0], ExpDataSchema.EXP_ID[0]]
            self.rxn_req_cols = [
                ExpDataSchema.BARCODE[0],
                ExpDataSchema.SEQLIB_IDENTIFIER[0],
                ExpDataSchema.SAMPLE_ID[0],
                ExpDataSchema.EXTRACTION_ID[0],
            ]
            self.rxn_unique_cols = [
                ExpDataSchema.BARCODE[0],
                ExpDataSchema.SEQLIB_IDENTIFIER[0],
            ]
            self.rxn_notblank_cols = [
                ExpDataSchema.SAMPLE_ID[0],
                ExpDataSchema.SEQLIB_IDENTIFIER[0],
                ExpDataSchema.PCR_IDENTIFIER[0],
                ExpDataSchema.SEQLIB_IDENTIFIER[0],
            ]
            self.barcode_pattern = "barcode[0-9]{2}"
        elif self.expt_type == "PCR":
            self.expt_req_cols = [ExpDataSchema.EXP_ID[0], ExpDataSchema.EXP_ID[0]]
            self.rxn_req_cols = [
                ExpDataSchema.PCR_IDENTIFIER[0],
                ExpDataSchema.SAMPLE_ID[0],
                ExpDataSchema.EXTRACTION_ID[0],
            ]
            self.rxn_unique_cols = [ExpDataSchema.PCR_IDENTIFIER[0]]
            self.rxn_notblank_cols = [
                ExpDataSchema.SAMPLE_ID[0],
                ExpDataSchema.EXTRACTION_ID[0],
                ExpDataSchema.PCR_IDENTIFIER[0],
            ]
            self.barcode_pattern = ""
        elif self.expt_type == "sWGA":
            self.expt_req_cols = [ExpDataSchema.EXP_ID[0], ExpDataSchema.EXP_ID[0]]
            self.rxn_req_cols = [
                ExpDataSchema.SWGA_IDENTIFIER[0],
                ExpDataSchema.SAMPLE_ID[0],
                ExpDataSchema.EXTRACTION_ID[0],
            ]
            self.rxn_unique_cols = [ExpDataSchema.SWGA_IDENTIFIER[0]]
            self.rxn_notblank_cols = [
                ExpDataSchema.SAMPLE_ID[0],
                ExpDataSchema.EXTRACTION_ID[0],
                ExpDataSchema.SWGA_IDENTIFIER[0],
            ]
            self.barcode_pattern = ""
        else:
            raise DataFormatError(
                f"Error experiment type given as {self.expt_type}, expected seqlib, PCR or sWGA."
            )

    def _check_number_rows(
        self, num_rows: int, df: pd.DataFrame, filename: Path
    ) -> int:
        """
        Check if correct number of rows are present in df

        Args:
            num_rows(int): Number of rows expected
            df(dataframe): dataframe to assess

        Returns:
            found_rows(int)
        """
        found_rows = df.shape[0]

        if found_rows != num_rows:
            log.info(f"WARNING: Expected {num_rows} rows, but found {found_rows}!")

        if found_rows == 0:
            raise DataFormatError(f"No rows found in {filename}!")

        return found_rows

    def _check_for_columns(self, columns: list, df: pd.DataFrame) -> None:
        """
        Check the correct columns are present

        Args:
            columns(list): List of column names
            df(dataframe): dataframe to assess
        """
        for c in columns:
            if c not in df:
                raise DataFormatError(f"Metadata must contain column called {c}!")

    def _check_entries_unique(self, columns: list, df: pd.DataFrame) -> None:
        """
        Check entires of the required columns are unique

        Args:
            columns(list): List of column names
            df(dataframe): dataframe to assess

        TODO: this will also disallow missing?
        """

        for c in columns:
            all_entries = df[c].tolist()
            observed_entries = []
            for entry in all_entries:
                if entry in observed_entries:
                    raise DataFormatError(
                        f"Column {c} entries should be unique, but {entry} is duplicated."
                    )
                observed_entries.append(entry)

    def _check_barcodes_valid(self) -> None:
        """
        Check the barcode entries are valid

        """
        for barcode in self.barcodes:
            if barcode == "unclassified":
                continue
            m = re.match(self.barcode_pattern, str(barcode))
            if m is None:
                raise DataFormatError(
                    f"Error in barcode name for {barcode}. To be valid, must match this regexp: {self.barcode_pattern}."
                )

    def _check_valid_date_format(self, date: str, format: str = "%Y-%m-%d") -> None:
        """Check that a `date` adheres to a given `format`"""
        try:
            datetime.strptime(date, format)
        except ValueError:
            raise DataFormatError(
                f"Date {date} does not adhere to expected format: {format}."
            )

    def _check_entries_not_blank(self, columns: list, df: pd.DataFrame) -> None:
        """
        Check that all entries in these columns are not blank

        Args:
            columns
            df (dataframe)
        """

        for c in columns:
            df_filtered = df[df[c].isnull()]
            if df_filtered.shape[0] > 0:
                raise DataFormatError(
                    f"Column {c} contains empty data for {self.expt_id}:\n{df_filtered}"
                )

    def _check_expt_id_fn_sheet(self) -> None:
        """
        Check that the expt_id in the filename is the same as the expt_id given in the spreadsheet
        """
        filename_expt_id = identify_exptid_from_path(self.filepath)

        if not filename_expt_id == self.expt_id:
            raise DataFormatError(
                f"Exp ID from filename ({filename_expt_id}) and spreadsheet tab ({self.expt_id}) do NOT match"
            )


class ExpMetadataMerge:
    """
    Extract metadata from multiple files, merge into a coherent dataframe, and optionally export the data
    """

    def __init__(self, filepaths: list[Path], output_folder: Path = None):
        # Pull in the dynamically created ExpDataSchema as an object
        ExpDataSchema = ExpDataSchemaFields()
        self.DataSchema = ExpDataSchema

        # Check that there aren't duplicate experiment IDs
        self._check_duplicate_expid(filepaths)

        # Output all data into a metadata subfolder for ease of use
        if output_folder:
            output_folder = output_folder / "experimental"
            produce_dir(output_folder)

        # Extract each file as an object into a dictionary
        expdata_dict = {
            identify_exptid_from_path(filepath): ExpMetadataParser(
                filepath, output_folder=output_folder
            )
            for filepath in filepaths
        }
        log.info(divider)

        # Concatenate all the exp level data into a df
        self.expts_df = pd.concat(expdata_dict[key].expt_df for key in expdata_dict)
        # Concatenate all the rxn level data into a df
        self.rxns_df = pd.concat(expdata_dict[key].rxn_df for key in expdata_dict)

        # Identify the expt_types present and create an empty df for each
        expt_df_dict = {
            expdata_dict[key].expt_type: pd.DataFrame for key in expdata_dict
        }
        # Create attribute of expt_types for knowing columns generated
        self.expt_types = list(expt_df_dict.keys())

        # Populate df with the appropriate entries and define the
        for expt_type in expt_df_dict.keys():
            # Concatenate data from the same expt_types into the dataframe dict
            expt_df_dict[expt_type] = pd.concat(
                expdata_dict[key].df
                for key in expdata_dict
                if expdata_dict[key].expt_type == expt_type
            )
            # Add instance attribute for each expt_type to self
            setattr(self, expt_type.lower() + "_df", expt_df_dict[expt_type])

        # Provide for a case where only a single expt type is present
        if len(self.expt_types) == 1:
            log.info(f"Only a single expt type ({expt_type}) identified")
            alldata_df = expt_df_dict[expt_type]
        else:
            # Create joins dict according to experiment types present
            joins = {}
            if "sWGA" in expt_df_dict and "PCR" in expt_df_dict:
                joins["sWGA and PCR"] = {
                    "joining": ["sWGA", "PCR"],
                    "left_df": expt_df_dict["sWGA"],
                    "right_df": expt_df_dict["PCR"],
                    "on": ExpDataSchema.SWGA_IDENTIFIER[0],
                    "cols": [
                        ExpDataSchema.SAMPLE_ID[0],
                        ExpDataSchema.EXTRACTION_ID[0],
                    ],
                    "suffixes": ["_sWGA", "_PCR"],
                    "mismatch_escape": (ExpDataSchema.SWGA_IDENTIFIER[0], "no swga"),
                }
            if "PCR" in expt_df_dict and "seqlib" in expt_df_dict:
                joins["PCR and seqlib"] = {
                    "joining": ["PCR", "seqlib"],
                    "left_df": expt_df_dict["PCR"],
                    "right_df": expt_df_dict["seqlib"],
                    "on": ExpDataSchema.PCR_IDENTIFIER[0],
                    "cols": [
                        ExpDataSchema.SAMPLE_ID[0],
                        ExpDataSchema.EXTRACTION_ID[0],
                    ],
                    "suffixes": ["_PCR", "_seqlib"],
                    "mismatch_escape": (ExpDataSchema.PCR_IDENTIFIER[0], "no pcr"),
                }

            log.info("Checking for data validity and merging dataframes for:")

            # Cycle through all of the joins required based on the data present. Enumerate from 1
            for count, join in enumerate(joins, start=1):
                # Load the current join from the dict
                join_dict = joins[join]
                log.info(f"   {join_dict['joining'][0]} and {join_dict['joining'][1]}")

                # Join the two df together
                data_df = pd.merge(
                    left=join_dict["left_df"],
                    right=join_dict["right_df"],
                    how="outer",
                    on=join_dict["on"],
                    suffixes=join_dict["suffixes"],
                    indicator=True,
                )

                # Create df with unmatched records from the right
                # NOT left as this would highlight all that have not been completed / advanced i.e. sWGA performed, but not PCR
                missing_records_df = data_df[data_df["_merge"] == "right_only"]

                # Identify names of key columns for reporting back to user and to check for mismatches
                # Above join appends suffix to column names so create correct list of names
                key_cols = [
                    item + suffix
                    for item in join_dict["cols"]
                    for suffix in join_dict["suffixes"]
                ]
                expt_id_cols = [
                    ExpDataSchema.EXP_ID[0] + suffix for suffix in join_dict["suffixes"]
                ]

                # Combine for user feedback and include the join column for quick referencing in spreadsheet
                show_cols = [join_dict["on"]] + expt_id_cols + key_cols

                # Ensure that only empty entries are mismatched and not those that should not have a match
                escape = join_dict.get("mismatch_escape", None)
                missing_records_df = missing_records_df[
                    missing_records_df[escape[0]].str.lower() != escape[1]
                ]

                # Give user feedback
                if len(missing_records_df) > 0:
                    warning = (
                        join_dict["joining"][1]
                        + " data missing from "
                        + join_dict["joining"][0]
                        + " data"
                    )
                    log.info(f"   WARNING: {warning}")
                    log.info(missing_records_df[show_cols].to_string(index=False))

                    # Output the missing data
                    if output_folder:
                        # to a folder called problematic
                        problematic_dir = output_folder / "problematic"
                        produce_dir(problematic_dir)
                        path = problematic_dir / f"{warning}.csv"
                        missing_records_df[show_cols].to_csv(path, index=False)
                        print(f"   Missing records written to {path}")
                    log.info("")

                # Create df with matched records
                matched_df = data_df[data_df["_merge"] == "both"]
                # Identify any mismatched records for the key columns
                for c in join_dict["cols"]:
                    # Pull out the two dataseries to compare
                    col1 = matched_df[f"{c}{join_dict['suffixes'][0]}"]
                    col2 = matched_df[f"{c}{join_dict['suffixes'][1]}"]
                    # Identify all that don't match
                    mismatches_df = matched_df.loc[(col1 != col2)]
                    # Feedback to user
                    if mismatches_df.shape[0] > 0:
                        log.info(f"   WARNING: Mismatches identified for {c}")
                        log.info(
                            f"   {mismatches_df[show_cols].to_string(index=False)}"
                        )
                        # Output the missmatched data
                        if output_folder:
                            # to a folder called problematic
                            problematic_dir = output_folder / "problematic"
                            produce_dir(problematic_dir)
                            path = problematic_dir / f"{c} mismatches.csv"
                            mismatches_df[show_cols].to_csv(path, index=False)
                            print(f"   Mismatched records written to {path}")
                        log.info("")
                        log.info("")

                # To ensure that all columns have the correct suffix, you need to rejoin the columns with or wthout
                # suffixes depending on whether it is the first (right hand df has no suffix) or last join (both given suffixes)
                # The following combos are possible SWGA-PCR, PCR-SEQLIB and / or both of them
                if len(joins) == 1:
                    # Single  merged so give all a suffix
                    alldata_df = pd.merge(
                        left=join_dict["left_df"],
                        right=join_dict["right_df"],
                        how="outer",
                        on=join_dict["on"],
                        suffixes=(join_dict["suffixes"]),
                    )
                elif count < len(joins):
                    # Another df to add so leave common fields without a suffix
                    alldata_df = pd.merge(
                        left=join_dict["left_df"],
                        right=join_dict["right_df"],
                        how="outer",
                        on=join_dict["on"],
                        suffixes=([join_dict["suffixes"][0], None]),
                    )
                else:
                    # Last df being merged so give all a suffix
                    alldata_df = pd.merge(
                        left=alldata_df,
                        right=join_dict["right_df"],
                        how="outer",
                        on=join_dict["on"],
                        suffixes=(join_dict["suffixes"]),
                    )

            # Collapse columns where multiple identical entries exist
            cols_2_collapse = [
                ExpDataSchema.SAMPLE_ID[0],
                ExpDataSchema.EXTRACTION_ID[0],
                ExpDataSchema.PCR_IDENTIFIER[0],
                ExpDataSchema.SWGA_IDENTIFIER[0],
                ExpDataSchema.SAMPLE_TYPE[0],
            ]

            alldata_df = collapse_repeat_columns(alldata_df, cols_2_collapse)

            # Remove the expt_type fields as they are not informative in a merged df
            dropcols = [
                col
                for col in alldata_df.columns
                if col.startswith(ExpDataSchema.EXP_TYPE[0])
            ]
            alldata_df.drop(dropcols, axis=1, inplace=True)

            # Fill in the nan values
            alldata_df_na = alldata_df.fillna("None")

            log.info("Summarising rxn performed")
            # Group and aggregate the df to give a list of all experiments performed on each sample
            col_roots = [
                ExpDataSchema.SAMPLE_ID[0],
                ExpDataSchema.EXTRACTION_ID[0],
                ExpDataSchema.PCR_ASSAY[0],
                ExpDataSchema.SWGA_IDENTIFIER[0],
                ExpDataSchema.PCR_IDENTIFIER[0],
                ExpDataSchema.SEQLIB_IDENTIFIER[0],
            ]
            collapsed_df = collapse_repeat_columns(alldata_df_na, col_roots)
            self.exp_summary_df = (
                collapsed_df[col_roots]
                .groupby([ExpDataSchema.SAMPLE_ID[0], ExpDataSchema.PCR_ASSAY[0]])
                .agg(list)
                .reset_index()
            )

        # Create an instance attribute
        self.all_df = alldata_df

        log.info("Done")
        log.info(divider)

        # Remove columns from expts_df
        expt_cols = [
            "expt_id",
            "expt_date",
            "expt_user",
            "expt_type",
            "expt_rxns",
            "expt_notes",
            "expt_summary",
        ]
        expt_summary_df = self.expts_df[expt_cols].sort_values(["expt_date"])

        # Optionally export the aggregate data
        if output_folder:
            identify_export_dataframe_attributes(self, output_folder)

        # Give user a summary of experiments performed
        log.info("Experiments performed:")
        log.info(expt_summary_df.to_string(index=False))
        log.info(divider)

    def _check_duplicate_expid(self, filepaths: list[Path]) -> None:
        """
        Checks for duplicate expids in list of filename paths

        Args:
            filepaths (list[Path]): List of Path objects

        """
        if isinstance(filepaths, str):
            filepaths = [filepaths]

        # Create an empty set and dict
        expid_dict = {}
        keys_seen = set()

        for filepath in filepaths:
            expid = identify_exptid_from_path(filepath)
            if expid in keys_seen:
                raise ValueError(
                    f"Duplicate expt_id identified: {expid} in files: {filepath.name} and {expid_dict[expid]}"
                )
            # Add to set for checking and to dict for printing out filename
            keys_seen.add(expid)
            expid_dict[expid] = filepath.name


@singleton
class SampleDataSchemaFields:
    """
    Pull in all of the dataschema fields
    """

    def __init__(self, csv_path: Path):
        # Get a list of all ini paths
        ini_files = identify_files_by_search(csv_path.parent, re.compile(".*.ini"))

        if len(ini_files) > 1:
            log.info(f"Multiple .ini files found, using first one: {ini_files[0].name}")
        self.dataschema_dict = create_dict_from_ini(ini_files[0])

        # Create simple dict of field and labels
        self.field_labels = reformat_nested_dict(self.dataschema_dict, "field", "label")

        # Iterate and set attributes
        for dict_key in self.dataschema_dict.keys():
            field_value = get_nested_key_value(self.dataschema_dict, dict_key, "field")
            label_value = get_nested_key_value(self.dataschema_dict, dict_key, "label")
            setattr(self, dict_key.upper(), (field_value, label_value))

        # Identify all with datatype entries
        self.dtypes = filter_nested_dict(
            self.dataschema_dict,
            new_key_field="field",
            new_value_field="datatype",
            exclude_value="date",
        )

        # Identify all that ARE dates
        self.datefields = filter_nested_dict(
            self.dataschema_dict,
            new_key_field="field",
            new_value_field="datatype",
            exclude_value="date",
            reverse=True,
        )

        # Identify all dates that have a defined format
        self.dateformats = filter_nested_dict(
            self.dataschema_dict, new_key_field="field", new_value_field="dateformat"
        )


class SampleMetadataParser:
    """
    Extract sample metadata from a single csv file, define fieldnames and labels,
    and determine experimental status of each sample (if passed data).

    """

    def __init__(
        self,
        metadata_file: Path,
        output_folder: Path = None,
    ):
        # Load dataschema for sample set and save as attribute
        SampleDataSchema = SampleDataSchemaFields(metadata_file)
        self.DataSchema = SampleDataSchema

        # load the data from the metadata file and ensure sampleID is a str
        # Don't use the user-defined dtypes when loading as causes errors - rather apply later
        if metadata_file.suffix.lower() == ".csv":
            df = pd.read_csv(metadata_file, dtype={SampleDataSchema.SAMPLE_ID[0]: str})
        elif metadata_file.suffix.lower() in (".xlsx", ".xls"):
            df = pd.read_excel(
                metadata_file, dtype={SampleDataSchema.SAMPLE_ID[0]: str}
            )
        else:
            raise DataFormatError(f"Unknown file type for {metadata_file}")

        # Filter out any missing sample_id's
        df = df[df[SampleDataSchema.SAMPLE_ID[0]].notna()]

        # Try to ensure fields are correct datatypes
        for key, value in SampleDataSchema.dtypes.items():
            try:
                df[key] = df[key].astype(value)
            except ValueError as e:
                log.info(f"Error converting column '{key}' to type '{value}': {e}")
        # Ensure dates are correctly formatted
        for datefield in SampleDataSchema.datefields:
            f = SampleDataSchema.dateformats.get(datefield, "")
            if f:
                df[datefield] = pd.to_datetime(df[datefield], format=f)
            else:
                df[datefield] = pd.to_datetime(df[datefield])

            # Check if dates parsed correctly
            if not pd.api.types.is_datetime64_dtype(df[datefield]):
                raise DataFormatError(f"Date errors in field / column: {datefield}")

        # Define attribute
        self.df = df

        # export data
        if output_folder:
            output_folder = output_folder / "samples"
            identify_export_dataframe_attributes(self, output_folder)

    def incorporate_experimental_data(self, ExpClassInstance):
        """
        Update df with status of each sample ie incorporate experiment data into sample df
        """
        print("Adding test status to sample metadata")
        df = ExpClassInstance.rxns_df
        # Define attributes from the ExpClassInstance
        exp_type_colname = ExpClassInstance.DataSchema.EXP_TYPE[0]
        exp_sampleid_colname = ExpClassInstance.DataSchema.SAMPLE_ID[0]
        rxn_df = ExpClassInstance.rxns_df
        # Import all the exp_types / status outcomes
        exp_types = ExpThroughputDataScheme.EXP_TYPES

        # Create new status column filled with 'not tested'
        sample_status_colname = self.DataSchema.STATUS[0]
        df[sample_status_colname] = exp_types[0]

        # Define all experiment types present
        exp_types_present = rxn_df[exp_type_colname].unique()

        for exp_type in exp_types:  # Ensure order is followed
            if exp_type in exp_types_present:
                # Get a set of sample_ids that have the same matching expt_type and ensure types are strings!
                samplelist = set(
                    rxn_df[rxn_df[exp_type_colname] == exp_type][
                        exp_sampleid_colname
                    ].astype(str)
                )
                # Enter result into df overwriting previous entries
                df.loc[
                    df[exp_sampleid_colname].isin(samplelist),
                    sample_status_colname,
                ] = exp_type

        # Replace with updated df
        self.df_with_exp = df


@singleton
class SeqDataSchemaFields:
    """
    Pull in all of the dataschema fields
    """

    def __init__(
        self,
    ):
        ini_files = identify_files_by_search(
            default_ini_folder, re.compile("seq_savanna.ini"), False, False
        )

        self.dataschema_dict = create_dict_from_ini(ini_files)

        self.field_labels = reformat_nested_dict(self.dataschema_dict, "field", "label")
        # Iterate and set attributes as a tuple with the field_name first and human label second
        for dict_key in self.dataschema_dict.keys():
            field_value = get_nested_key_value(self.dataschema_dict, dict_key, "field")
            label_value = get_nested_key_value(self.dataschema_dict, dict_key, "label")
            setattr(self, dict_key.upper(), (field_value, label_value))

        # Define list of fields for mapped list
        self.READS_MAPPED_TYPE = [
            value["field"]
            for value in self.dataschema_dict.values()
            if "reads_mapped_type" in value
        ]


class SequencingMetadataParser:
    """
    Extract all identifiable sequencing data from nomadic / savanna pipelines.

    """

    def __init__(
        self,
        seqdata_folder: Path,
        output_folder: Path = None,
    ):
        # Load dataschema for sample set and save as an object attribute
        SeqDataSchema = SeqDataSchemaFields()
        self.DataSchema = SeqDataSchema

        log.info("   Searching for bamstats file(s)")
        bamfiles = identify_files_by_search(
            seqdata_folder, Regex_patterns.SEQDATA_BAMSTATS_CSV, recursive=True
        )
        summary_bam = concat_files_add_expID(bamfiles, SeqDataSchema.EXP_ID[0])
        self.summary_bam = summary_bam

        log.info("   Searching for bedcov file(s)")
        bedcovfiles = identify_files_by_search(
            seqdata_folder, Regex_patterns.SEQDATA_BEDCOV_CSV, recursive=True
        )
        # Remove any with nomadic in path as this output is identically named in nomadic and savanna and only want latter
        bedcovfiles = [x for x in bedcovfiles if "nomadic" not in str(x)]
        summary_bedcov = concat_files_add_expID(bedcovfiles, SeqDataSchema.EXP_ID[0])
        self.summary_bedcov = summary_bedcov

        log.info("   Searching for sample QC file(s)")
        exptqcfiles = identify_files_by_search(
            seqdata_folder, Regex_patterns.SEQDATA_QC_PER_SAMPLE_CSV, recursive=True
        )
        qc_per_sample = concat_files_add_expID(exptqcfiles, SeqDataSchema.EXP_ID[0])
        self.qc_per_sample = qc_per_sample

        log.info("   Searching for experiment QC file(s)")
        qc_per_expt_files = identify_files_by_search(
            seqdata_folder, Regex_patterns.SEQDATA_QC_PER_EXPT_JSON, recursive=True
        )
        qc_per_expt = concat_files_add_expID(qc_per_expt_files, SeqDataSchema.EXP_ID[0])
        # Add in additional calculations not made from savanna
        qc_per_expt[SeqDataSchema.PERCENT_SAMPLES_PASSEDCOV[0]] = (
            qc_per_expt[SeqDataSchema.N_SAMPLES_PASS_COV_THRSHLD[0]]
            / qc_per_expt[SeqDataSchema.N_SAMPLES[0]]
        ) * 100
        qc_per_expt[SeqDataSchema.PERCENT_SAMPLES_PASSEDCONT[0]] = (
            qc_per_expt[SeqDataSchema.N_SAMPLES_PASS_CONTAM_THRSHLD[0]]
            / qc_per_expt[SeqDataSchema.N_SAMPLES[0]]
        ) * 100
        self.qc_per_expt = qc_per_expt

        if output_folder:
            output_folder = output_folder / "sequence"
            identify_export_dataframe_attributes(self, output_folder)

    def incorporate_experimental_data(self, ExpClassInstance):
        """
        Expand sequence data metrics with the addition of sample and experimental data
        """
        # Define the expdataschema object
        ExpDataSchema = ExpClassInstance.DataSchema

        # Filter expdataschema to key fields needed
        key_fields_dict = filter_dict_by_key_or_value(
            ExpDataSchema.dataschema_dict,
            ["EXP_ID", "SAMPLE_ID", "EXTRACTIONID", "BARCODE", "SAMPLE_TYPE"],
            search_key=True,
        )

        # Simplify dict to a list of keys (fieldnames in df)
        key_fields = list(
            reformat_nested_dict(key_fields_dict, "field", "label").keys()
        )

        # Need to match the sequence data outputs to the exp.rxn_df to merge correctly
        # Make a deep copy of the df and then remove all entries that do not relate to
        # a sequencing experiment
        match_df = ExpClassInstance.rxns_df.copy()
        match_df = match_df[match_df["expt_type"] == "seqlib"]

        # Trim to key_fields that are present
        match_df = match_df[[col for col in key_fields if col in match_df.columns]]
        match_df = match_df.sort_values(by=["expt_id", "barcode"])

        # Add in field if missing
        if ExpDataSchema.SAMPLE_TYPE[0] not in match_df.columns:
            match_df[ExpDataSchema.SAMPLE_TYPE[0]] = np.nan

        # Define the colnames that are needed for matching seqdata to expdata
        cols_to_match = [
            self.DataSchema.EXP_ID[0],
            self.DataSchema.BARCODE[0],
            ExpDataSchema.EXP_ID[0],
            ExpDataSchema.BARCODE[0],
        ]

        summary_bam = merge_additional_rxn_level_fields(
            self.summary_bam, match_df, cols_to_match
        )
        self.summary_bam_with_exp = summary_bam

        summary_bedcov = merge_additional_rxn_level_fields(
            self.summary_bedcov, match_df, cols_to_match
        )
        self.summary_bedcov_with_exp = summary_bedcov

        qc_per_sample = merge_additional_rxn_level_fields(
            self.qc_per_sample, match_df, cols_to_match
        )

        # Add in info on sample type if not supplied from the template
        qc_per_sample[ExpDataSchema.SAMPLE_TYPE[0]] = qc_per_sample.apply(
            lambda row: row[ExpDataSchema.SAMPLE_TYPE[0]]
            if pd.notnull(row[ExpDataSchema.SAMPLE_TYPE[0]])
            else (
                "Positive"
                if row["is_positive"]
                else ("Negative" if row["is_negative"] else "Field")
            ),
            axis=1,
        )
        qc_per_sample.drop(
            columns=[self.DataSchema.ISPOS[0], self.DataSchema.ISNEG[0]], inplace=True
        )
        self.qc_per_sample_with_exp = qc_per_sample

        # Merge the exptqc and bam outputs and drop repeat columns
        summary_bamqc = pd.merge(
            left=self.summary_bam,
            right=self.qc_per_sample,
            on=[self.DataSchema.BARCODE[0], self.DataSchema.EXP_ID[0]],
            how="outer",
        )
        summary_bamqc = collapse_repeat_columns(
            summary_bamqc,
            [self.DataSchema.SAMPLE_ID[0], self.DataSchema.SAMPLE_TYPE[0]],
        )
        self.summary_bamqc = summary_bamqc


@singleton
class Combine_Exp_Seq_Sample_data:
    """
    Merge all data sources
    """

    def __init__(
        self, exp_data, sequence_data, sample_data, output_folder: Path = None
    ):
        # Pull in all of the dataschemas from the different sources
        ExpDataSchema = exp_data.DataSchema
        SeqDataSchema = sequence_data.DataSchema
        SampleDataSchema = sample_data.DataSchema

        # Combine the exp and seq data
        alldata_df = pd.merge(
            exp_data.all_df,
            sequence_data.summary_bamqc,
            left_on=[
                ExpDataSchema.BARCODE[0],
                ExpDataSchema.EXP_ID_SEQLIB[0],
                ExpDataSchema.SAMPLE_ID[0],
            ],
            right_on=[
                SeqDataSchema.BARCODE[0],
                SeqDataSchema.EXP_ID[0],
                SeqDataSchema.SAMPLE_ID[0],
            ],
            how="outer",
        )
        # Ensure sample_id is a string
        alldata_df[ExpDataSchema.SAMPLE_ID[0]] = alldata_df[
            ExpDataSchema.SAMPLE_ID[0]
        ].astype("string")

        # Add in the sample data
        alldata_df = pd.merge(
            alldata_df,
            sample_data.df,
            left_on=[ExpDataSchema.SAMPLE_ID[0]],
            right_on=[SampleDataSchema.SAMPLE_ID[0]],
            how="outer",
        )

        # Collapse all  repeat columns
        dup_cols = identify_duplicate_colnames(
            exp_data.all_df, sequence_data.summary_bamqc, sample_data.df
        )
        alldata_df = collapse_repeat_columns(alldata_df, dup_cols)

        # Combine the dataschemas
        all_dataschema_dict = (
            ExpDataSchema.dataschema_dict
            | SampleDataSchema.dataschema_dict
            | SeqDataSchema.dataschema_dict
        )

        # Ensure that all columns are in the dataschema
        fields = [value["field"] for value in all_dataschema_dict.values()]
        unknown_cols = [x for x in alldata_df.columns if x not in fields]
        # Sample data can have columns not identified in the .ini file so remove these
        unknown_cols = [
            x for x in unknown_cols if x not in list(sample_data.df.columns)
        ]
        if len(unknown_cols) > 0:
            raise DataFormatError(
                f"WARNING: {unknown_cols} columns are not defined in the dataschemas. Ensure they are defined in the .ini files."
            )

        # Define df as an attribute
        self.df = alldata_df
        # define list of refs for dropdowns
        self.datasources_dict = {
            "sWGA": "Experimental (sWGA)",
            "PCR": "Experimental (PCR)",
            "seqlib": "Experimental (seqlib)",
            "sample": "Sample information",
            "seqdata": "Sequence Analysis (savanna  )",
        }

        # List of variable names for each data source
        self.datasource_fields = {
            "sWGA": ExpDataSchema.sWGA_field_labels,
            "PCR": ExpDataSchema.PCR_field_labels,
            "seqlib": ExpDataSchema.seqlib_field_labels,
            "sample": SampleDataSchema.field_labels,
            "seqdata": SeqDataSchema.field_labels,
        }

        # List of all field label combos
        self.dataschema_dict = (
            ExpDataSchema.dataschema_dict
            | SampleDataSchema.dataschema_dict
            | SeqDataSchema.dataschema_dict
        )

        # Collapse into a list of all field and labels for any translations
        all_field_labels = {}
        for dict_value in self.datasource_fields.values():
            all_field_labels = all_field_labels | dict_value
        self.all_field_labels = all_field_labels

        if output_folder:
            identify_export_dataframe_attributes(self, output_folder)


class ExpThroughputDataScheme:
    #### Definitions for making the summary throughput calculations #####
    # TODO: Add these into the above classes dataschemas?
    SAMPLES = "experiments"
    EXPERIMENTS = "reactions"
    REACTIONS = "samples"
    # Define as a tuple so it is ordered and immutable
    EXP_TYPES = ("Not tested", "sWGA", "PCR", "seqlib")
