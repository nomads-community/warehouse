import json
import logging
import pathlib as Path
from itertools import chain

import pandas as pd
from tabulate import tabulate

from warehouse.lib.exceptions import DataFormatError
from warehouse.lib.general import (
    identify_exptid_from_path,
    produce_dir,
)

# Get logging process
log = logging.getLogger("dataframes")


def collapse_repeat_columns(df: pd.DataFrame, field_roots: list) -> pd.DataFrame:
    """
    Merging dataframes creates duplicated fields that only differ by a suffix e.g. _pcr
    or _x. These need to be collapsed so that a single column captures the details needed.

    Args:
        df (pd.DataFrame): The pandas DataFrame to collapse columns in.
        field_roots (list): List of root fieldnames e.g. sample_id

    Returns:
        df (pd.DataFrame): The pandas DataFrame with the duplicate columns dropped.
    """

    # Copy df so there aren't any slice conflicts
    df = df.copy(deep=True)

    for root in field_roots:
        # Identify all the fields
        repeat_cols = [col for col in df.columns if col.startswith(root)]
        # Stack all entries for columns, then take the first entry (not null) of each group ie assumes they are identical
        # Reindex in case all columns have an empty value, which should never happen, but better to be safe
        df["interim"] = (
            df[repeat_cols].stack().groupby(level=0).first().reindex(df.index)
        )
        # Remove all repeat columns
        df.drop(columns=repeat_cols, inplace=True)
        # Rename interim to original
        df.rename(columns={"interim": root}, inplace=True)

    return df


def identify_duplicate_colnames(*args) -> list:
    """
    Identifies column names found in two or more dataframes

    params:
        *args: df1, df2, df3 ...
            list of dataframes

    returns
        list of colnames
    """

    # Add all colnames into a single list
    colnames = list()
    for df in args:
        df_cols = list(df.columns)
        colnames = colnames + df_cols

    # return non-unique entries
    return [i for i in set(colnames) if colnames.count(i) > 1]


def count_non_none_entries_in_dfcolumn(df: pd.DataFrame, column: str) -> int:
    """
    Function counts the number of non none entries in a column of a dataframe
    Args:
        df (pd.DataFrame): The pandas DataFrame to export.
        column (str): Name of the column to assess

    Returns:
        int : Count of entries in the column that are not None.
    """

    return len(
        [
            item
            for item in list(chain.from_iterable(df[f"{column}"]))
            if not item == "None"
        ]
    )


def export_df_to_csv(df: pd.DataFrame, folder: Path, filename: str) -> None:
    """
    Export a pandas df to a csv file
    Args:
        df (pd.DataFrame): The pandas DataFrame to export.
        folder (Path): Path object folder where the CSV will be saved.
        filename (str):  .csv filename to be created.

    Returns:
        None
    """

    path = folder / filename
    df.to_csv(path, index=False)


def identify_export_class_attributes(obj, output_dir):
    """
    Outputs all attributes of an object that are DataFrames as individual CSV files.

    Args:
        obj: The object whose attributes to inspect.
        output_dir: The directory where the CSV files will be saved.
    """
    log.debug("   Exporting attributes:")
    for attr_name in [a for a in dir(obj) if not a.startswith("__")]:
        attr = getattr(obj, attr_name)
        csv_file = f"{output_dir}/{attr_name}.csv"

        if isinstance(attr, set):
            attr = pd.DataFrame(sorted(list(attr)), columns=[f"{attr_name}_elements"])
            attr.to_csv(csv_file, index=False)
            log.debug(f"      set: '{attr_name}' saved to {csv_file}")
        if isinstance(attr, pd.DataFrame):
            produce_dir(output_dir)
            attr.to_csv(csv_file, index=False)
            log.debug(f"     dataframe: '{attr_name}' saved to {csv_file}")


def merge_additional_rxn_level_fields(
    main_df: pd.DataFrame,
    exp_seq_df: pd.DataFrame,
    colnames: list[str],
    how: str = "left",
) -> pd.DataFrame:
    """
    Function to merge in additional experimental data to a df.

    Args:
        main_df (df):  df to have additional data added to
        exp_seq_df (df):   Experimental data Dataframe to extract data from
        colnames list(str): colnames for left_exp_id, left_barcode, right_exp_id, right_barcode
        how(str): How to merge e.g. left, right, inner, etc. Default is 'left'
    """
    if len(colnames) != 4:
        log.info("Incorrect number of entries given")

    if how not in ["left", "right", "inner", "outer"]:
        raise ValueError(
            f"Invalid merge type: {how}. Must be one of 'left', 'right', 'inner', or 'outer'."
        )

    if main_df.empty:
        raise DataFormatError("The main_df is empty")

    if exp_seq_df.empty:
        raise DataFormatError("The exp_seq_df is empty")

    df = pd.merge(
        left=main_df,
        right=exp_seq_df,
        left_on=[colnames[0], colnames[1]],
        right_on=[colnames[2], colnames[3]],
        how="outer",
        indicator=True,
    )

    # Ensure duplicate columns are collapsed to a single one
    df = collapse_repeat_columns(df, ["sample_id", "expt_id", "barcode"])

    exp_details_missing_df = df.query("_merge == 'left_only'").drop(columns="_merge")
    seq_details_missing_df = df.query("_merge == 'right_only'").drop(columns="_merge")

    # Warn user if data not matching between the two dataframes
    if not exp_details_missing_df.empty:
        exp_ids = list(exp_details_missing_df[colnames[0]].unique())
        log.warning(f"Warning: {exp_ids} missing matching experimental detail data.")
        log.debug(tabulate_df(exp_details_missing_df))

    if not seq_details_missing_df.empty:
        exp_ids = list(seq_details_missing_df[colnames[0]].unique())
        log.warning(f"Warning: {exp_ids} missing matching sequence detail data.")
        log.debug(tabulate_df(seq_details_missing_df))

    # Remove unnecessary entries
    if how == "left":
        df = df[df["_merge"] != "right_only"]
    elif how == "right":
        df = df[df["_merge"] != "left_only"]
    elif how == "inner":
        df = df[df["_merge"] == "both"]

    # Drop merge col
    df.drop(columns="_merge", inplace=True)

    return df


def concat_files_add_expID(
    files: list[Path], EXP_ID_COL: str = "expt_id"
) -> pd.DataFrame:
    """
    Function to extract and concatenate multiple files of the same type into a df.

    Args:
        files list(Path):  List of Path names
        EXP_ID_COL (str):   Column name for experimental ID
    """
    # Create empty df to add data to and list of expids
    df = pd.DataFrame()
    expids = []
    # Extract data, add in experiment ID and concatenate all data
    for file in files:
        expid = identify_exptid_from_path(file, raise_error=False)

        # Ensure there is an expid
        if not expid:
            log.warning(f"No ExpID identified for {file}, skipping...")
            continue

        # Process according to filetype
        if file.suffix == ".csv":
            data = pd.read_csv(file)
            data[EXP_ID_COL] = expid
        elif file.suffix == ".tsv":
            data = pd.read_csv(file, sep="\t")
            data[EXP_ID_COL] = expid
        elif file.suffix == ".json":
            with open(file, "r") as f:
                json_dict = json.load(f)
            data = pd.DataFrame(json_dict, index=[expid]).reset_index()
            data.rename(columns={"index": EXP_ID_COL}, inplace=True)
        else:
            raise DataFormatError(f"Unsupported file type: {file.suffix}")
        if expid in expids:
            duplicates = [str(f.parent) for f in files if expid in str(f)]
            raise DataFormatError(
                f"{expid} duplicate experiment ID detected in {duplicates}"
            )

        # Add expid to list
        expids.append(expid)
        # Concatenate data if not empty
        if data.shape[0] > 0:
            df = pd.concat([df, data], ignore_index=True)
    return df


def filtered_dataframe(
    df: pd.DataFrame, colname: str, values: list[str]
) -> pd.DataFrame:
    """
    Filters the DataFrame based on the selected experiment IDs.

    Args:
        df (pd.DataFrame): The DataFrame to filter
        colname (str): The column name to filter on
        values (list): The values to filter the colname for

    Returns:
        pd.DataFrame: The filtered DataFrame.
    """

    df_filtered = df.query(f"{colname} in @values")
    return df_filtered


def dataframe_not_empty(df) -> bool:
    """
    Checks if a DataFrame or Series is not empty.

    Args:
        df (pd.DataFrame): The DataFrame to check.

    Returns:
        bool: True if the DataFrame is not empty, False otherwise.
    """
    return not df.empty


def tabulate_df(
    df: pd.DataFrame,
    maxcolwidth: int = 30,
    tablefmt: str = "grid",
    colalign: str = "center",
) -> str | None:
    """
    Converts a DataFrame to a tabulate format for better readability.

    Args:
        df (pd.DataFrame): The DataFrame to convert.
        maxcolwidth (int): The maximum column width for the tabulated output.
        tablefmt (str): The format of the table (e.g., 'grid', 'plain').
        colalign (str): The alignment for all columns ('left', 'center', 'right

    Returns:
        str: The tabulated string representation of the DataFrame.
    """
    if df.empty:
        return None
    max_col_widths = [maxcolwidth] * len(df.columns)
    colaligns = [colalign] * len(df.columns)

    return tabulate(
        df,
        headers="keys",
        colalign=colaligns,
        tablefmt=tablefmt,
        maxcolwidths=max_col_widths,
        showindex=False,
        missingval="N/A",
    )
