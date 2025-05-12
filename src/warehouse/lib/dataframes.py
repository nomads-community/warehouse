import json
import logging
import pathlib as Path
from itertools import chain

import pandas as pd

from warehouse.lib.exceptions import DataFormatError
from warehouse.lib.general import identify_exptid_from_path, produce_dir

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


def identify_export_dataframe_attributes(obj, output_dir):
    """
    Outputs all attributes of an object that are DataFrames as individual CSV files.

    Args:
        obj: The object whose attributes to inspect.
        output_dir: The directory where the CSV files will be saved.
    """
    log.info("   Exporting dataframe attributes:")
    for attr_name in dir(obj):
        attr = getattr(obj, attr_name)
        if isinstance(attr, pd.DataFrame):
            produce_dir(output_dir)
            csv_file = f"{output_dir}/{attr_name}.csv"
            attr.to_csv(csv_file, index=False)
            log.info(f"      '{attr_name}' saved to {csv_file}")
    log.info("   Done")


def merge_additional_rxn_level_fields(
    main_df: pd.DataFrame, exp_seq_df: pd.DataFrame, colnames: list[str]
) -> pd.DataFrame:
    """
    Function to merge in additional experimental data to a df.

    Args:
        main_df (df):  df to have additional data added to
        exp_seq_df (df):   Experimental data Dataframe to extract data from
        colnames list(str): colnames for left_exp_id, left_barcode, right_exp_id, right_barcode
    """
    if len(colnames) != 4:
        log.info("Incorrect number of entries given")

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
        log.info(f"   {exp_details_missing_df}")

    if not seq_details_missing_df.empty:
        exp_ids = list(seq_details_missing_df[colnames[0]].unique())
        log.warning(f"Warning: {exp_ids} missing matching sequence detail data.")
        log.info(f"   {seq_details_missing_df}")

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
        expid = identify_exptid_from_path(file)
        if file.suffix == ".csv":
            data = pd.read_csv(file)
            data[EXP_ID_COL] = expid

        if file.suffix == ".json":
            with open(file, "r") as f:
                json_dict = json.load(f)
            data = pd.DataFrame(json_dict, index=[expid]).reset_index()
            data.rename(columns={"index": EXP_ID_COL}, inplace=True)

        if expid in expids:
            raise DataFormatError(f"{expid} duplicate experiment ID detected: ")

        # Add expid to list
        expids.append(expid)

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
