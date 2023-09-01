import os
import re
from pathlib import Path, PurePath
import pandas as pd

from .exceptions import MetadataFormatError


class ExpMetadataParser:
    """
    Parse the experimental and individual rxn metadata, and make sure that it is formatted
    correctly

    """
    EXPT_REQUIRED_COLUMNS = ["expt_id", "expt_date"]
    RXN_REQUIRED_COLUMNS = ["barcode", "seqlib_id", "sample_id","extraction_id"]
    RXN_UNIQUE_COLUMNS = ["barcode", "seqlib_id"]
    BARCODE_PATTERN = "barcode[0-9]{2}"

    def __init__(self, metadata_folder: str, expt_id: str = None, include_unclassified: bool = False):
        """
        Load and sanity check the metadata

        """
        self.metadata_folder = Path(metadata_folder)
        self.expt_id = expt_id

        print(f"Searching for {expt_id} metadata files in {self.metadata_folder}..." )
        #Load and check expt metadata
        self.expt_csv = self._match_file(self.expt_id + "_expt_metadata.csv")
        self.expt_df = pd.read_csv(self.expt_csv)
        self._check_for_columns(self.EXPT_REQUIRED_COLUMNS, self.expt_df)
        self._check_for_rows(1, self.expt_df)
        self.num_rxn = self.expt_df["seqlib_rxns"].iloc[0]
        self.expt_date = self.expt_df["expt_date"].iloc[0]
        self.expt_summary = self.expt_df["expt_summary"].iloc[0]
        print("      Passed formatting checks.")

        #Load and check rxn metadata
        self.rxn_csv = self._match_file(self.expt_id + "_rxn_metadata.csv")
        self.rxn_df = pd.read_csv(self.rxn_csv)
        self._check_for_columns(self.RXN_REQUIRED_COLUMNS, self.rxn_df)
        self._check_for_rows(self.num_rxn, self.rxn_df)
        self._check_entries_unique(self.RXN_UNIQUE_COLUMNS, self.rxn_df)
        print("      Passed formatting checks.")

        print("Merging experimental and rxn data...")
        self.df = pd.merge(self.expt_df, self.rxn_df, on='expt_id', how='inner')
        self.barcodes = self.df["barcode"].tolist()
        if include_unclassified:
            self.barcodes.append("unclassified")
        self._check_barcodes_valid()

        print("      Done")

    def _match_file(self, searchstring):

        """
        Identify if there is a matching file for the given expt_id
        """

        searchstring = re.compile(searchstring)
        matching_files = [ path for path in self.metadata_folder.iterdir()
                          if searchstring.match(path.name) ]

        if len(matching_files) != 1:
            raise MetadataFormatError(f"Expected to find 1 file, but {count} were found")
        else:
            match_path = matching_files[0]
            print(f"   Found: {PurePath(match_path).name}")

        return match_path

    def _check_for_rows(self, num_rows, dataframe):
        """
        Check if correct number of rows are present

        """
        found_rows = dataframe.shape[0]
        if found_rows != num_rows:
            raise MetadataFormatError(f"Expected {num_rows} rows, but found {found_rows}!")

    def _check_for_columns(self, columns, dataframe):
        """
        Check the correct columns are present

        """
        for c in columns:
            if not c in dataframe:
                raise MetadataFormatError(f"Metadata must contain column called {c}!")

    def _check_entries_unique(self, columns, dataframe):
        """
        Check entires of the required columns are unique

        TODO: this will also disallow missing?

        """

        for c in columns:
            all_entries = dataframe[c].tolist()
            observed_entries = []
            for entry in all_entries:
                if entry in observed_entries:
                    raise MetadataFormatError(
                        f"Column {c} entries should be unique, but {entry} is duplicated."
                    )
                observed_entries.append(entry)

    def _check_barcodes_valid(self):
        """
        Check the barcode entries are valid

        """
        for barcode in self.barcodes:
            if barcode == "unclassified":
                continue
            m = re.match(self.BARCODE_PATTERN, barcode)
            if m is None:
                raise MetadataFormatError(f"Error in barcode name for {barcode}. To be valid, must match this regexp: {self.BARCODE_PATTERN}.")
