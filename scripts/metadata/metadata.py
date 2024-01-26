import re
from pathlib import Path
import pandas as pd
from datetime import datetime
from itertools import chain
from lib.exceptions import MetadataFormatError

class ExpMetadataParser:
    """
    Parse and validate the experimental and individual rxn metadata from an individual Excel spreadsheet.

    """
    
    def __init__(self, metadata_file: Path, include_unclassified: bool = False):
        """
        Load and sanity check the metadata

        """
        print(f"{metadata_file.name}")
        self.tabnames = ["expt_metadata", "rxn_metadata"]

        #Extract sheetnames
        sheets = pd.ExcelFile(metadata_file).sheet_names
        #Check both sheets / tabs are present
        if not (self.tabnames[0] in sheets and self.tabnames[1] in sheets):
            raise MetadataFormatError(f"Missing tabs in {metadata_file}")

        #Load expt metadata
        self.expt_df = self._extract_excel_data(metadata_file, self.tabnames[0])
        self.expt_id = self.expt_df["expt_id"].iloc[0]
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
        self.rxn_df = self._extract_excel_data(metadata_file, self.tabnames[1])
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

        print(f"      Merging experimental and rxn data for {self.expt_id}...")
        self.df = pd.merge(self.expt_df, self.rxn_df, on='expt_id', how='inner')
        print("Done")

    def _extract_excel_data(self, filename, tabname):

            """
            Extract data from valid Excel sheets and return a dataframe.
            """

            #Extract data and drop empty rows
            data =  pd.read_excel(filename, sheet_name=tabname)
            data.dropna(how='all', inplace=True)

            return data

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
            if c not in df:
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
            
    
class ExpMetadataMerge:
    """
    Extract metadata from multiple files, merge into a coherent dataframe, and optionally export the data
    """
    def __init__(self, matching_filepaths, output_folder : Path):
        #Extract each file into a dictionary 
        metadata_dict = { self._identify_exptid_from_fn(filepath) : ExpMetadataParser(filepath) for filepath in matching_filepaths }
        print("="*80)
        
        #Concatenate all the data for the different experimental types
        #TO DO: Make it more flexible in case there are none of a certain type of expt
        sWGA_df = pd.concat(metadata_dict[key].df for key in metadata_dict if metadata_dict[key].expt_type == "sWGA" )
        PCR_df = pd.concat(metadata_dict[key].df for key in metadata_dict if metadata_dict[key].expt_type == "PCR" )
        seqlib_df = pd.concat(metadata_dict[key].df for key in metadata_dict if metadata_dict[key].expt_type == "seqlib" )
        # print(f"Total rxns identified by experiment type:")
        # print(f"   sWGA:{sWGA_df.shape[0]}")
        # print(f"   PCR:{PCR_df.shape[0]}")
        # print(f"   seqlib:{seqlib_df.shape[0]}")
        # print("="*80)

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
        #Fill in the nan values so the aggregation works
        allmetadata_df = allmetadata_df.fillna('None')
        # Group and aggregate the df to give a list of all experiments performed on each sample 
        self.agg_experiments_df = allmetadata_df[cols_to_retain].groupby(['sample_id', 'expt_assay']).agg(list).reset_index()

        #Give some user feedback on number of reactions performed
        print("   Total reactions:")
        identifier_cols = [col for col in self.agg_experiments_df.columns if 'identifier' in col]

        for col in identifier_cols:
            value = self._count_non_none_entries_in_dfcolumn(self.agg_experiments_df, col)
            name = col.replace("_identifier","")
            print(f"      {name}: {value}")
        print("Done")
        print("="*80)

        #Optionally export the data
        if output_folder:
            print(f"Outputting data to folder: {output_folder.name}")
            #Iterate through the dictionary outputting individual and aggregate
            for key in metadata_dict:
                print(f"   {key}")
                #Experiment
                expt_df = metadata_dict[key].expt_df
                expt_fn = f"{key}_expt_metadata.csv"
                expt_path = output_folder / expt_fn
                expt_df.to_csv(expt_path, index=False)
                #Reaction
                rxn_df = metadata_dict[key].rxn_df
                rxn_fn = f"{key}_rxn_metadata.csv"
                rxn_path = output_folder / rxn_fn
                rxn_df.to_csv(rxn_path, index=False)
            
            #Aggregate
            agg_fn = "aggregate_metadata.csv"
            agg_path = output_folder / agg_fn
            self.agg_experiments_df.to_csv(agg_path, index=False)  
            
            print("Done")
            print("="*80)
        

        
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

    def _count_non_none_entries_in_dfcolumn (self, df, column):
        '''
        Function counts the number of non none entries in a column of a dataframe
        '''
        
        return len([item for item in list(chain.from_iterable(df[f"{column}"])) if not item=="None"])

    def _identify_exptid_from_fn(self, filepath):
        """
        Extract the experimental ID from a filename
        """
        id_regex = '(SW|PC|SL)[a-zA-Z]{2}\d{3}'
        match = re.search(id_regex, filepath.name)
        if match: 
            expt_id = match.group(0)
        else:
            raise MetadataFormatError(f"Unable to determine the ExpID from the filename for {filepath.name}")
        return expt_id