import logging
import re
from dataclasses import dataclass, field
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
    create_datasources_dict,
    create_dict_from_yaml,
    filter_dict_by_key_or_value,
    merge_dataschema_dicts_with_suffixes,
    reformat_nested_dict,
)
from warehouse.lib.exceptions import DataFormatError
from warehouse.lib.general import (
    extract_exptype_from_expid,
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


@dataclass
class SchemaParser:
    """
    Generate a dataschema from a yaml file

    Attributes:
        schema_details (list):
            A list consisting of the name of the schema and the path to the YAML file

        fields (dict):
            A dict containing all the yaml entries in the format:
                ATTRIBUTE_NAME : {field: FIELDNAME, label: LABEL}
                EXPID : {field : exp_id, label: Experiment ID}

        dtypes (dict):
            A dict containing all of the defined datatypes for a field in the format:
                FIELDNAME : DATATYPE
                age : int

        dateformats(dict):
            A dict containing all of the fields with defined dateformat in the format:
                FIELDNAME : DATEFORMAT
                collection_date : %Y/%m/%d

        DYNAMIC_ATTRIBUTES(tuples)
            All entries from the fields are added as individual attributes in the format:
                self.ATTRIBUTENAME = ( FIELDNAME, LABEL)
                self.EXPID = (exp_id, Experiment ID)

    """

    schema_details: list
    fields: dict = field(init=False)
    dtypes: dict = field(init=False)
    dateformats: dict = field(init=False)

    def __post_init__(self):
        # Extract the data from the yaml file
        _yaml_fields = create_dict_from_yaml(self.schema_details[1])

        # Set attributes for each of the fields and add to dict
        self.fields = {}
        self.dtypes = {}
        self.dateformats = {}
        for key, dict in _yaml_fields.items():
            # Get field labels and set attributes
            field = dict.get("field")
            label = dict.get("label")
            setattr(self, key.upper(), (field, label))
            self.fields[key] = {"field": field, "label": label}
            # Get datatype and date format fields
            if dict.get("datatype"):
                self.dtypes[field] = dict.get("datatype")
            if dict.get("dateformat"):
                self.dateformats[field] = dict.get("dateformat")


@dataclass
class DataSchema:
    """
    Generate one or more dataschemas from defined yaml files

    Attributes:
        files (list):
            A list of information and filepath for dataschema YAML files in the format:
                CATEGORY: {category_label: CATEGORY_LABEL,
                            sources: SOURCENAME,
                            source_labels: SOURCE_LABEL,
                            paths: PATHS}
                experimental: {category_label: Experimental Data,
                            sources: [pcr, seqlib],
                            source_labels: [PCR, Sequencing],
                            paths: [dataschemas/PCR.yml, dataschemas/seqlib.yml] }
        categories (dict)
            Dict of all categories present in the format:
                CATEGORY : CATEGORY_LABEL
                experimental: Experimental data

        sources (dict)
            Dict of all sources present in the format:
                CATEGORY : { SOURCENAME : SOURCELABEL}
                experimental: {PCR: PCR experiment data, seqlib: Sequencing data}

        dataschemas (dict)
            This dict houses all the individual SchemaParser objects as:
                SOURCENAME: SchemaParserObj
                PCR: SchemaParserObj_for_PCR.yml file

        dataschema (dict)
            This dict merges all of the dataschemas into a single dict and adds suffixes
            to duplicate fields
                ATTRIBUTE_NAME : {field: FIELDNAME, label: LABEL}
                EXPID_PCR : {field : exp_id_pcr, label: Experiment ID}

        DYNAMIC_ATTRIBUTES(tuples)
            All entries from the dataschema dict are added as individual attributes in the format:
                self.ATTRIBUTENAME = ( FIELDNAME, LABEL)
                self.EXPID = (exp_id, Experiment ID)
    """

    files: dict
    categories: dict = field(init=False)
    sources: dict = field(init=False)
    dataschemas: dict = field(init=False)

    def __post_init__(self):
        # Initialise attributes so they are not empty
        self.categories = {}
        self.sources = {}
        self.dataschemas = {}

        # Process each category of data
        for category, cat_values in self.files.items():
            # Add category labels
            self.categories[category] = cat_values.get("category_label")

            log.debug(f"Category = {category}")
            # Process each source
            for source, source_label, path in zip(
                cat_values["sources"],
                cat_values["source_labels"],
                cat_values["paths"],
            ):
                log.debug(
                    f"source = {source}, source_label = {source_label}, path = {path}"
                )
                # Generate the information on this source
                _entry = {source: source_label}
                # Add to the _sources dict
                if self.sources.get(category):
                    # Add to exisiting entry when present
                    self.sources[category].update(_entry)
                else:
                    # Create a new entry if not
                    self.sources[category] = _entry

                # Generate schema from YAML file and add to dataschemas
                self.dataschemas[source] = SchemaParser([source, path])

            # Merge all source dataschemas together and add suffixes where there is a conflict
            dict_list = [dict.fields for dict in self.dataschemas.values()]
            suffix_list = list(self.dataschemas.keys())
            self.dataschema = merge_dataschema_dicts_with_suffixes(
                dict_list, suffix_list
            )

            # Create dataschema attributes
            for key, dict in self.dataschema.items():
                setattr(
                    self,
                    key.upper(),
                    (dict.get("field"), dict.get("label")),
                )


class ExpMetadataParser:
    """
    Parse and validate the experimental and individual rxn metadata from an individual Excel spreadsheet.

    """

    def __init__(
        self,
        file_path: Path,
        ExpDataSchema: DataSchema,
        output_folder: Path = None,
        include_unclassified: bool = False,
    ):
        """
        Load and sanity check the metadata

        """
        log.info(f"{file_path.name}")

        # Identify experiment ID from filename
        expt_id = identify_exptid_from_path(file_path)
        # Determine expt type from expid
        expt_type_fn = extract_exptype_from_expid(expt_id)

        # Get correct dataschema for the exp type
        self.DataSchema = ExpDataSchema.dataschemas.get(expt_type_fn)

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
        self.expt_id = self.expt_df[self.DataSchema.EXP_ID[0]].iloc[0]
        self.expt_date = self.expt_df[self.DataSchema.EXP_DATE[0]].iloc[0]
        self._check_valid_date_format(self.expt_date)
        self.expt_summary = self.expt_df[self.DataSchema.EXP_SUMMARY[0]].iloc[0]
        self.expt_type = self.expt_df[self.DataSchema.EXP_TYPE[0]].iloc[0]
        # Save the number of samples entered into the assay tab
        num_rxn = self.expt_df[self.DataSchema.EXP_RXNS[0]].iloc[0]
        # Check validity of expt data
        ###################
        self._define_expt_variables()
        self._check_for_columns(self.expt_req_cols, self.expt_df)
        self._check_number_rows(1, self.expt_df, self.filepath)
        self._check_expt_id_fn_sheet()
        expected_colnames = set(
            item["field"] for item in self.DataSchema.fields.values()
        )
        self._check_all_colnames_known(expected_colnames)
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
            self.barcodes = self.rxn_df[self.DataSchema.BARCODE[0]].tolist()
            if include_unclassified:
                self.barcodes.append("unclassified")
            self._check_barcodes_valid()
        log.info("      Rxn metadata passed formatting checks.")

        log.info(f"      Merging experimental and rxn data for {self.expt_id}...")
        self.df = pd.merge(self.expt_df, self.rxn_df, on="expt_id", how="inner")
        # Add expt_type back into the rxn dataframe after the merge otherwise there
        # will be duplicate expt_type cols
        self.rxn_df[self.DataSchema.EXP_TYPE[0]] = self.rxn_df.get(
            self.DataSchema.EXP_TYPE[0], self.expt_type
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

        if self.expt_type == "seqlib":
            self.expt_req_cols = [self.DataSchema.EXP_ID[0], self.DataSchema.EXP_ID[0]]
            self.rxn_req_cols = [
                self.DataSchema.BARCODE[0],
                self.DataSchema.SEQLIB_IDENTIFIER[0],
                self.DataSchema.SAMPLE_ID[0],
                self.DataSchema.EXTRACTION_ID[0],
            ]
            self.rxn_unique_cols = [
                self.DataSchema.BARCODE[0],
                self.DataSchema.SEQLIB_IDENTIFIER[0],
            ]
            self.rxn_notblank_cols = [
                self.DataSchema.SAMPLE_ID[0],
                self.DataSchema.SEQLIB_IDENTIFIER[0],
                self.DataSchema.PCR_IDENTIFIER[0],
                self.DataSchema.SEQLIB_IDENTIFIER[0],
            ]
            self.barcode_pattern = "barcode[0-9]{2}"
        elif self.expt_type == "PCR":
            self.expt_req_cols = [self.DataSchema.EXP_ID[0], self.DataSchema.EXP_ID[0]]
            self.rxn_req_cols = [
                self.DataSchema.PCR_IDENTIFIER[0],
                self.DataSchema.SAMPLE_ID[0],
                self.DataSchema.EXTRACTION_ID[0],
            ]
            self.rxn_unique_cols = [self.DataSchema.PCR_IDENTIFIER[0]]
            self.rxn_notblank_cols = [
                self.DataSchema.SAMPLE_ID[0],
                self.DataSchema.EXTRACTION_ID[0],
                self.DataSchema.PCR_IDENTIFIER[0],
            ]
            self.barcode_pattern = ""
        elif self.expt_type == "sWGA":
            self.expt_req_cols = [self.DataSchema.EXP_ID[0], self.DataSchema.EXP_ID[0]]
            self.rxn_req_cols = [
                self.DataSchema.SWGA_IDENTIFIER[0],
                self.DataSchema.SAMPLE_ID[0],
                self.DataSchema.EXTRACTION_ID[0],
            ]
            self.rxn_unique_cols = [self.DataSchema.SWGA_IDENTIFIER[0]]
            self.rxn_notblank_cols = [
                self.DataSchema.SAMPLE_ID[0],
                self.DataSchema.EXTRACTION_ID[0],
                self.DataSchema.SWGA_IDENTIFIER[0],
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
        Check columns have unique entries

        Args:
            columns(list): List of column names
            df(dataframe): dataframe to assess
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

    def _check_all_colnames_known(self, colnames: set) -> None:
        """
        Check that all fields in the dataframe are present in the dataschema
        """
        # Identify all columns in the df
        df_cols = set(self.expt_df.columns)
        # Find any not in the expected colnames
        missing_fields = df_cols - colnames
        if len(missing_fields) > 0:
            raise DataFormatError(
                f"Fields {missing_fields} not found in dataschema, but present in {self.filepath.name}"
            )


class ExpMetadataMerge:
    """
    Extract metadata from multiple files, merge into a coherent dataframe, and optionally export the data
    """

    def __init__(
        self,
        exp_folder: Path,
        output_folder: Path = None,
    ):
        # Get the relevent dataschema
        dataschema_files = create_datasources_dict()
        ExpDataSchema = DataSchema(
            filter_dict_by_key_or_value(dataschema_files, "experimental")
        )
        self.dataschema = ExpDataSchema
        exp_fns = identify_files_by_search(
            exp_folder, Regex_patterns.NOMADS_EXP_TEMPLATE, recursive=True
        )
        # Check that there aren't duplicate experiment IDs
        self._check_duplicate_expid(exp_fns)

        # Output all data into a metadata subfolder for ease of use
        if output_folder:
            output_folder = output_folder / "experimental"
            produce_dir(output_folder)

        # Extract each file as an object into a dictionary
        expdata_dict = {
            identify_exptid_from_path(filepath): ExpMetadataParser(
                filepath, output_folder=output_folder, ExpDataSchema=ExpDataSchema
            )
            for filepath in exp_fns
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
                        log.info(f"   Missing records written to {path}")
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
                            log.info(f"   Mismatched records written to {path}")
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
        # Get the relevent dataschema
        dataschema_files = create_datasources_dict(metadata_file)
        SampleDataSchema = DataSchema(
            filter_dict_by_key_or_value(dataschema_files, "metadata")
        )
        self.DataSchema = SampleDataSchema

        # Save dataschema as attribute
        self.DataSchema = SampleDataSchema
        # load the data from the metadata file and ensure sampleID is a str
        # Don't use the user-defined dtypes when loading as causes errors - rather apply later
        if metadata_file.suffix.lower() == ".csv":
            df = pd.read_csv(metadata_file, dtype={SampleDataSchema.STUDY_ID[0]: str})
        elif metadata_file.suffix.lower() in (".xlsx", ".xls"):
            df = pd.read_excel(metadata_file, dtype={SampleDataSchema.STUDY_ID[0]: str})
        else:
            raise DataFormatError(f"Unknown file type for {metadata_file}")

        # Filter out any missing sample_id's
        df = df[df[SampleDataSchema.STUDY_ID[0]].notna()]

        # Update datatypes and dateformats
        for dataschema in SampleDataSchema.dataschemas.values():
            # Try to ensure fields are correct datatypes
            if hasattr(dataschema, "dtypes"):
                for key, value in dataschema.dtypes.items():
                    try:
                        df[key] = df[key].astype(value)
                    except ValueError as e:
                        log.info(
                            f"Error converting column '{key}' to type '{value}': {e}"
                        )
            if hasattr(dataschema, "dateformat"):
                # Ensure dates are correctly formatted
                for dateformat in dataschema.datefields:
                    f = dataschema.dateformats.get(dateformat, "")
                    if f:
                        df[dateformat] = pd.to_datetime(df[dateformat], format=f)
                    else:
                        df[dateformat] = pd.to_datetime(df[dateformat])

                    # Check if dates parsed correctly
                    if not pd.api.types.is_datetime64_dtype(df[dateformat]):
                        raise DataFormatError(
                            f"Date errors in field / column: {dateformat}"
                        )

        # Define attribute
        self.df = df.copy(deep=True)

        # Remove any columns not listed in the dataschema
        cols_to_drop = list(
            set(df.columns)
            - set(f["field"] for f in SampleDataSchema.dataschema.values())
        )
        df.drop(columns=cols_to_drop, inplace=True, errors="ignore")
        self.df = df

        # export data
        if output_folder:
            output_folder = output_folder / "samples"
            identify_export_dataframe_attributes(self, output_folder)

    def incorporate_experimental_data(
        self, ExpClassInstance: ExpMetadataMerge, output_folder: Path
    ):
        """
        Update df with status of each sample ie incorporate experiment data into sample df
        """
        log.info("Adding test status to sample metadata")

        # Define attributes from the ExpClassInstance
        exp_type_colname = ExpClassInstance.dataschema.EXP_TYPE[0]
        exp_sampleid_colname = ExpClassInstance.dataschema.SAMPLE_ID[0]
        rxn_df = ExpClassInstance.rxns_df
        # Import all the exp_types / status outcomes
        exp_types = ExpThroughputDataScheme.EXP_TYPES

        # Create a copy of the df to ensure original is not modified
        df = self.df.copy()

        # Create new status column filled with 'not tested'
        sample_status_colname = self.DataSchema.STATUS[0]
        df[sample_status_colname] = exp_types[0]

        # Define the sample_id column
        sample_id_colname = self.DataSchema.STUDY_ID[0]

        for exp_type in exp_types:  # Ensure order is followed
            if exp_type in ExpClassInstance.expt_types:
                # Get a set of sample_ids that have the same matching expt_type and ensure types are strings!
                samplelist = set(
                    rxn_df[rxn_df[exp_type_colname] == exp_type][
                        exp_sampleid_colname
                    ].astype(str)
                )

                # Enter result into sample_df overwriting previous entry
                df.loc[
                    df[sample_id_colname].isin(samplelist),
                    sample_status_colname,
                ] = exp_type

        # Add updated df
        self.df_with_exp = df

        if output_folder:
            output_folder = output_folder / "samples"
            identify_export_dataframe_attributes(self, output_folder)


class SequencingMetadataParser:
    """
    Extract all identifiable sequencing data from nomadic / savanna pipelines.

    """

    def __init__(
        self,
        seqdata_folder: Path,
        output_folder: Path = None,
    ):
        # Get the relevent dataschema
        dataschema_files = create_datasources_dict()
        SeqDataSchema = DataSchema(
            filter_dict_by_key_or_value(dataschema_files, "savanna")
        )
        # Save dataschema as an attribute
        self.DataSchema = SeqDataSchema

        log.info("   Searching for bamstats file(s)")
        bamfiles = identify_files_by_search(
            seqdata_folder, Regex_patterns.SEQDATA_BAMSTATS_CSV, recursive=True
        )
        self.summary_bam = concat_files_add_expID(bamfiles, SeqDataSchema.EXP_ID[0])

        log.info("   Searching for bedcov file(s)")
        bedcovfiles = identify_files_by_search(
            seqdata_folder, Regex_patterns.SEQDATA_BEDCOV_CSV, recursive=True
        )
        # Remove any with nomadic in path as this output is identically named in nomadic and savanna and only want latter
        bedcovfiles = [x for x in bedcovfiles if "nomadic" not in str(x)]
        self.summary_bedcov = concat_files_add_expID(
            bedcovfiles, SeqDataSchema.EXP_ID[0]
        )

        log.info("   Searching for sample QC file(s)")
        exptqcfiles = identify_files_by_search(
            seqdata_folder, Regex_patterns.SEQDATA_QC_PER_SAMPLE_CSV, recursive=True
        )
        self.qc_per_sample = concat_files_add_expID(
            exptqcfiles, SeqDataSchema.EXP_ID[0]
        )

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
        qc_per_expt[SeqDataSchema.PERCENT_SAMPLES_PASSEDCONTAM[0]] = (
            qc_per_expt[SeqDataSchema.N_SAMPLES_PASS_CONTAM_THRSHLD[0]]
            / qc_per_expt[SeqDataSchema.N_SAMPLES[0]]
        ) * 100
        self.qc_per_expt = qc_per_expt

        log.info("   Searching for bcftools file(s)")
        bcftools_files = identify_files_by_search(
            seqdata_folder, Regex_patterns.SEQDATA_BCFTOOLS_OUTPUT_TSV, recursive=True
        )

        self.bcftools = concat_files_add_expID(bcftools_files, SeqDataSchema.EXP_ID[0])

        if output_folder:
            output_folder = output_folder / "sequence"
            identify_export_dataframe_attributes(self, output_folder)

    def incorporate_experimental_data(self, ExpClassInstance):
        """
        Expand sequence data metrics with the addition of sample and experimental data
        """
        # Define the expdataschema object
        ExpDataSchema = ExpClassInstance.dataschema
        # Filter expdataschema to key fields needed
        key_fields_dict = filter_dict_by_key_or_value(
            ExpDataSchema.dataschema,
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
        self,
        exp_data: ExpMetadataMerge,
        sequence_data: SequencingMetadataParser,
        sample_data: SampleMetadataParser,
        output_folder: Path = None,
    ):
        # Pull in all of the dataschemas from the different sources
        ExpDataSchema = exp_data.dataschema
        SeqDataSchema = sequence_data.DataSchema
        SampleDataSchema = sample_data.DataSchema

        log.debug("   Combining experimental and sequence data to alldata_df:")
        alldata_df = pd.merge(
            exp_data.all_df,
            sequence_data.summary_bamqc,
            left_on=[
                ExpDataSchema.BARCODE[0],
                f"{ExpDataSchema.EXP_ID[0]}_seqlib",
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

        log.debug("   Adding in the sample data to alldata_df")
        alldata_df = pd.merge(
            alldata_df,
            sample_data.df,
            left_on=[ExpDataSchema.SAMPLE_ID[0]],
            right_on=[SampleDataSchema.STUDY_ID[0]],
            how="outer",
        )

        log.debug("   Collapsing duplicate columns in alldata_df")
        # Collapse all repeat columns
        dup_cols = identify_duplicate_colnames(
            exp_data.all_df, sequence_data.summary_bamqc, sample_data.df
        )
        alldata_df = collapse_repeat_columns(alldata_df, dup_cols)

        log.debug("Combining dataschemas")
        self.dataschema = (
            ExpDataSchema.dataschema
            | SeqDataSchema.dataschema
            | SampleDataSchema.dataschema
        )

        self.categories = (
            ExpDataSchema.categories
            | SeqDataSchema.categories
            | SampleDataSchema.categories
        )

        self.sources = (
            ExpDataSchema.sources | SeqDataSchema.sources | SampleDataSchema.sources
        )

        _dataschemas = (
            ExpDataSchema.dataschemas
            | SeqDataSchema.dataschemas
            | SampleDataSchema.dataschemas
        )
        _fields = {}
        for key, ds in _dataschemas.items():
            curr_ds = reformat_nested_dict(ds.fields, "field", "label")
            _fields[key] = curr_ds
        self.fields = _fields

        log.info("   Checking that dataschema and dataframe correlate")
        ds_fields = [d["field"] for d in self.dataschema.values()]
        unknown_cols = [x for x in alldata_df.columns if x not in ds_fields]
        log.debug("   Removing sample data columns not listed in the YAML file")
        unknown_cols = [
            x for x in unknown_cols if x not in list(sample_data.df.columns)
        ]
        if len(unknown_cols) > 0:
            raise DataFormatError(
                f"WARNING: {unknown_cols} are not defined in the dataschemas. Add to the relevent YAML file"
            )

        # Remove entries from the dataschema that are not relevent
        keys_to_delete = []
        for key, value in self.dataschema.items():
            if value["field"] not in alldata_df.columns:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self.dataschema[key]

        log.debug(" Adding alldata_df as an attribute")
        self.df = alldata_df

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
