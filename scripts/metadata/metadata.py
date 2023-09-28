import re
from pathlib import Path, PurePath
import pandas as pd
from datetime import datetime
from itertools import chain

class MetadataFormatError(Exception):
    """Error in format or contents of the metadata"""
    pass

class ExpMetadataParser(MetadataFormatError):
    """
    Parse the experimental and individual rxn metadata, and make sure that it is formatted
    correctly. Requires two inputs:

    metadata_folder - Folder containing standardised csv files exported from individual experimental templates
    expt_id - The id of the experiment e.g. SLMM009

    """
    
    def __init__(self, metadata_folder: str, expt_id: str = None, include_unclassified: bool = False):
        """
        Load and sanity check the metadata

        """
        self.metadata_folder = Path(metadata_folder)
        self.expt_id = expt_id

        print(f"Searching for {expt_id} metadata files in {self.metadata_folder}..." )
        #Load expt metadata
        self.expt_csv = self._match_file(self.expt_id + "_expt_metadata.csv")
        self.expt_df = pd.read_csv(self.expt_csv, keep_default_na=False).dropna(how='all')
        self.expt_date = self.expt_df["expt_date"].iloc[0]
        self._check_valid_date_format(self.expt_date)
        self.expt_summary = self.expt_df["expt_summary"].iloc[0]
        self.expt_type = self.expt_df["expt_type"].iloc[0]
        self.num_rxn = self.expt_df["expt_rxns"].iloc[0]

        #Check validity of expt metadata
        self._define_expt_variables()
        self._check_for_columns(self.expt_req_cols, self.expt_df)
        self.expt_rows = self._check_number_rows(1, self.expt_df)
        print("      Experimental metadata file passed formatting checks.")

        #Load rxn metadata
        self.rxn_csv = self._match_file(self.expt_id + "_rxn_metadata.csv")
        self.rxn_df = pd.read_csv(self.rxn_csv, keep_default_na=False,).dropna(how='all')
        #Check validity of rxn metadata
        self._check_for_columns(self.rxn_req_cols, self.rxn_df)
        self.rxn_rows = self._check_number_rows(self.num_rxn, self.rxn_df)
        self._check_entries_unique(self.rxn_unique_cols, self.rxn_df)
        self._check_entries_not_blank(self.rxn_notblank_cols, self.rxn_df)
        if len(self.barcode_pattern) > 0  :
            self.barcodes = self.rxn_df["barcode"].tolist()
            if include_unclassified:
                self.barcodes.append("unclassified")
            self._check_barcodes_valid()
        print("      Rxn metadata file passed formatting checks.")

        print(f"   Merging experimental and rxn data for {expt_id}...")
        self.df = pd.merge(self.expt_df, self.rxn_df, on='expt_id', how='inner')
        print("      Done")
    
    def _match_file(self, searchstring):

        """
        Identify if there is a matching file for the given expt_id
        """

        searchstring = re.compile(searchstring)
        matching_files = [ path for path in self.metadata_folder.iterdir()
                          if searchstring.match(path.name) ]
        
        count = len(matching_files)            
        if count != 1:
            raise MetadataFormatError(f"Expected to find 1 file, but {count} were found")
        else:
            match_path = matching_files[0]
            print(f"   Found: {PurePath(match_path).name}")

        return match_path

    def _define_expt_variables(self):
        """
        Define all required fields, counts etc for the exp type.

        """
        print(f"      Identified as {self.expt_type} type experiment")
        self.rxn_identifier_col = self.expt_type + "_identifier"
        if self.expt_type == "seqlib":
            self.expt_req_cols = ["expt_id", "expt_date"]
            self.rxn_req_cols = ["barcode", "seqlib_identifier", "sample_id","extraction_id"]
            self.rxn_unique_cols = ["barcode", "seqlib_identifier"]
            self.rxn_notblank_cols = ["sample_id","extraction_id","swga_identifier", "pcr_identifier","seqlib_identifier"]
            self.barcode_pattern = "barcode[0-9]{2}"
        elif self.expt_type == "PCR":
            self.expt_req_cols = ["expt_id", "expt_date"]
            self.rxn_req_cols = ["pcr_identifier", "sample_id","extraction_id"]
            self.rxn_unique_cols = ["pcr_identifier"]
            self.rxn_notblank_cols = ["sample_id","extraction_id","swga_identifier", "pcr_identifier"]
            self.barcode_pattern = ""
        elif self.expt_type == "sWGA":
            self.expt_req_cols = ["expt_id", "expt_date"]
            self.rxn_req_cols = ["swga_identifier", "sample_id","extraction_id"]
            self.rxn_unique_cols = ["swga_identifier"]
            self.rxn_notblank_cols = ["sample_id","extraction_id","swga_identifier"]
            self.barcode_pattern = ""
        else:
            raise MetadataFormatError(f"Error experiment type given as {self.expt_type}, expected seqlib, PCR or sWGA.")
        
    def _check_number_rows(self, num_rows, df):
        """
        Check if correct number of rows are present

        """
        found_rows = df.shape[0]
        if found_rows != num_rows:
            print(f"WARNING: Expected {num_rows} rows, but found {found_rows}!")
            # raise MetadataFormatError(f"Expected {num_rows} rows, but found {found_rows}!")

    def _check_for_columns(self, columns, df):
        """
        Check the correct columns are present

        """
        for c in columns:
            if not c in df:
                raise MetadataFormatError(f"Metadata must contain column called {c}!")

    def _check_entries_unique(self, columns, df):
        """
        Check entires of the required columns are unique

        TODO: this will also disallow missing?

        """

        for c in columns:
            all_entries = df[c].tolist()
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
            m = re.match(self.barcode_pattern, str(barcode))
            if m is None:
                raise MetadataFormatError(f"Error in barcode name for {barcode}. To be valid, must match this regexp: {self.barcode_pattern}.")

    def _check_valid_date_format(self, date: str, format: str="%Y-%m-%d") -> None:
        """ Check that a `date` adheres to a given `format` """
        try:
            datetime.strptime(date, format)
        except ValueError:
            raise MetadataFormatError(f"Date {date} does not adhere to expected format: {format}.")
    
    def _check_entries_not_blank(self, columns, df):
        """
        Check that all entries in these columns are not blank
        """
        
        for c in columns:
            df_filtered = df[df[c].isnull()]
            if df_filtered.shape[0] >0 :
                print(f"WARNING: Column {c} contains empty data for {self.expt_id}:\n{df_filtered}")
            
class ExpMetadataMerge(ExpMetadataParser):
    def __init__(self, metadata_folder, exp_ids):
        metadata_dict = { expid: ExpMetadataParser(metadata_folder, expid) for expid in exp_ids }
        
        print("="*80)
        #Concatenate all the data for the different experimental types
        sWGA_df = pd.concat(metadata_dict[key].df for key in metadata_dict if metadata_dict[key].expt_type == "sWGA" )
        PCR_df = pd.concat(metadata_dict[key].df for key in metadata_dict if metadata_dict[key].expt_type == "PCR" )
        seqlib_df = pd.concat(metadata_dict[key].df for key in metadata_dict if metadata_dict[key].expt_type == "seqlib" )

        print("Checking for mismatches in the data between experiments:")
        # Right joins check if any of the right_df do NOT have a match in the left_df 
        self._check_entry_mismatch(pd.merge(left=sWGA_df,right=PCR_df,how="right",on="swga_identifier")
                                   ,['sample_id','extraction_id'])
        self._check_entry_mismatch(pd.merge(left=PCR_df,right=seqlib_df,how="right",on="pcr_identifier")
                                   ,['sample_id','extraction_id'])
        # Inner joins check to see if there are any mismatches where there is a join between the left_df and right_df
        self._check_entry_mismatch(pd.merge(left=sWGA_df,right=PCR_df,how="inner",on="swga_identifier")
                                   ,['sample_id','extraction_id'])
        self._check_entry_mismatch(pd.merge(left=PCR_df,right=seqlib_df,how="inner",on="swga_identifier")
                                   ,['sample_id','extraction_id'])
        print("Done")
        print("="*80)

        print("Aggregating all experimental data")
        allmetadata_df = pd.merge(left=sWGA_df,right=PCR_df,how="outer",on="swga_identifier", suffixes=('', '_pcr'))
        allmetadata_df = pd.merge(left=allmetadata_df,right=seqlib_df,how="outer",on="pcr_identifier", suffixes=('', '_seqlib'))

        cols_to_retain = ['sample_id', 'extraction_id', 'swga_identifier', 'expt_assay', 'pcr_identifier',
                          'seqlib_identifier']
        
        # Group and aggregate the df to give a list of all experiments performed on each sample 
        agg_experiments_df = allmetadata_df[cols_to_retain].groupby(['sample_id', 'expt_assay']).agg(list).reset_index()
        identifier_cols = [col for col in agg_experiments_df.columns if 'identifier' in col]

        #Give some user feedback on number of reactions performed
        for col in identifier_cols:
            value = self._count_non_nan_entries_in_dfcolumn(agg_experiments_df, col)
            name = col.replace("_identifier","")
            print(f"      {name}: {value}")

        # Output file for user
        output_path = Path.joinpath(Path(metadata_folder), "summary_rxn_data.csv")
        print(f"Outputting aggregated data to {output_path}")
        agg_experiments_df.to_csv(output_path, index=False)
        
    def _check_entry_mismatch(self, df, columns):
        """
        Check that data is in agreement for supplied columns 
        """
        
        for c in columns:
            #Identify mismatches and show the errors
            mismatches_df = df.loc[(df[f"{c}_x"] != df[f"{c}_y"]) ]
            cols_to_retain = ['expt_id_x','expt_id_y', f"{c}_x", f"{c}_y"]
            if mismatches_df.shape[0] > 0:
                print(f"WARNING: Mismatches identified for {c}")
                print(mismatches_df[cols_to_retain])

    def _count_non_nan_entries_in_dfcolumn (self, df, column):
        '''
        Function counts the number of non nan entries in a column of a dataframe
        '''
        
        return len([item for item in list(chain.from_iterable(df[f"{column}"])) if not pd.isna(item)])


    