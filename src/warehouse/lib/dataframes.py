import pandas as pd
import pathlib as Path
from itertools import chain


def collapse_columns(df: pd.DataFrame, field_roots: list) -> pd.DataFrame:
    """
    Merging dataframes creates duplicated fields that only differ by a suffix e.g. _pcr
    or _x. These need to be collapsed so that a single column captures the details needed.

    Args:
        df (pd.DataFrame): The pandas DataFrame to collapse columns in.
        field_roots (list): List of root fieldnames e.g. sample_id

    Returns:
        df (pd.DataFrame): The pandas DataFrame with the duplicate columns dropped.
    """

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
