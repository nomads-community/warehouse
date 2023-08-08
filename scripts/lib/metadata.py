import os
import re
import pandas as pd

from .exceptions import MetadataFormatError


class MetadataTableParser:
    """
    Parse the `metadata_csv` table, and make sure that it is formatted
    correctly

    """

    REQUIRED_COLUMNS = ["barcode", "seq_id", "sample_id"]
    UNIQUE_COLUMNS = ["seq_id"]
    BARCODE_PATTERN = "barcode[0-9]{2}"
    FIXED_ENTRIES = ["assay", "expt_date", "expt_id"]

    def __init__(self, metadata_csv: str, assay: str = None, expt_date: str = None, expt_id: str = None, include_unclassified: bool = False):
        """
        Load and sanity check the metadata table

        """

        self.csv = metadata_csv
        self.df = pd.read_csv(self.csv)
        self.assay = assay
        self.expt_date = expt_date
        self.expt_id = expt_id

        self._check_for_columns()
        self._check_entries_unique()

        self.barcodes = self.df["barcode"].tolist()
        if include_unclassified:
            self.barcodes.append("unclassified")
        self._check_barcodes_valid()

        self._check_fixedentries()


    def _check_for_columns(self):
        """
        Check the correct columns are present

        """

        for c in self.REQUIRED_COLUMNS:
            if not c in self.df.columns:
                raise MetadataFormatError(f"Metadata must contain column called {c}!")

    def _check_entries_unique(self):
        """
        Check entires of the required columns are unique

        TODO: this will also disallow missing?

        """

        for c in self.UNIQUE_COLUMNS:
            all_entries = self.df[c].tolist()
            observed_entries = []
            for entry in all_entries:
                if entry in observed_entries:
                    raise MetadataFormatError(
                        f"Column {c} must contain only unique entries, but {entry} is duplicated."
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

    def _check_fixedentries(self):
        """
        Check and compile the entries that are fixed

        """

        for c in self.FIXED_ENTRIES:
            clivalue = getattr(self,c)
            #Identify and load metadata supplied entry
            if c in self.df.columns:
                entries = self.df[c].unique().tolist()
                count = len(entries)
                #Check only one entry
                if  count > 1 :
                    raise MetadataFormatError(
                            f"Column {c} must contain a single unique entry, but there are {count} entries: {entries}"
                        )
                else:
                    metavalue = entries[0]

                #Compare cli and meta values, use metavalue if no clivalue
                if clivalue is not None :
                    if clivalue != metavalue:
                        raise MetadataFormatError(f"Metadata and CLI entry do not match for {c}")
                else:
                    setattr(self, c, metavalue)
            else:
                print(f"   {c} not identified in metadata")
