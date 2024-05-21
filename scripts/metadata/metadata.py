import re
from pathlib import Path
import pandas as pd
from datetime import datetime
from itertools import chain
from lib.exceptions import MetadataFormatError
from lib.general import identify_exptid_from_fn, identify_files_by_search, Regex_patterns

class ExpMetadataParser:
    """
    Parse and validate the experimental and individual rxn metadata from an individual Excel spreadsheet.

    """
    
    def __init__(self, metadata_file: Path, 
                 output_folder : Path = None,
                 include_unclassified: bool = False):
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
        print("      Experimental metadata passed formatting checks.")

        #Load rxn metadata
        self.rxn_df = self._extract_excel_data(metadata_file, self.tabnames[1])
        self.rxn_df['expt_type'] = pd.Series([self.expt_type] * len(self.rxn_df) )

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
        print("      Rxn metadata passed formatting checks.")

        print(f"      Merging experimental and rxn data for {self.expt_id}...")
        self.df = pd.merge(self.expt_df, self.rxn_df, on='expt_id', how='inner')

        if output_folder is not None:
            print(f"      Outputting data to folder: {output_folder.name}")
            output_dict = { "expt" : self.expt_df, "rxn" : self.rxn_df }
            for output in output_dict:
                filename = self.expt_id + "_" + output + "_metadata.csv"
                path = output_folder / filename
                output_dict[output].to_csv(path, index=False)
                
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
            self.rxn_notblank_cols = ["sample_id","extraction_id", "pcr_identifier","seqlib_identifier"]
            self.barcode_pattern = "barcode[0-9]{2}"
        elif self.expt_type == "PCR":
            self.expt_req_cols = ["expt_id", "expt_date"]
            self.rxn_req_cols = ["pcr_identifier", "sample_id","extraction_id"]
            self.rxn_unique_cols = ["pcr_identifier"]
            self.rxn_notblank_cols = ["sample_id","extraction_id", "pcr_identifier"]
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
                raise MetadataFormatError(f"Column {c} contains empty data for {self.expt_id}:\n{df_filtered}")          
    
class ExpMetadataMerge:
    """
    Extract metadata from multiple files, merge into a coherent dataframe, and optionally export the data
    """
    def __init__(self, matching_filepaths, output_folder : Path):
        #Extract each file into a dictionary 
        metadata_dict = { identify_exptid_from_fn(filepath) : ExpMetadataParser(filepath, output_folder=output_folder) for filepath in matching_filepaths }
        print("="*80)
        
        #Check that there aren't duplicate experiment IDs 
        dupes = self._check_duplicate_entries(metadata_dict, "expt_id")
        if dupes :
            raise ValueError(f"{len(dupes)} duplicate expt_id identfied: {dupes}")

        #Concatenate all the exp level data into a df
        self.expt_metadata_df = pd.concat(metadata_dict[key].expt_df for key in metadata_dict )
        #Concatenate all the rxn level data into a df
        self.rxn_metadata_df = pd.concat(metadata_dict[key].rxn_df for key in metadata_dict )

        # Create summaries of number of experiments and rxn performed
        exp_counts = self.expt_metadata_df['expt_type'].value_counts().rename("experiments")
        rxn_counts = self.rxn_metadata_df['expt_type'].value_counts().rename("reactions")
        #sample_counts = sample_df['status'].value_counts().rename("samples")
        #colour_series = pd.Series(colours, index=types).rename("colours")

        # na cause the datatype to change to a float so combine all ints and change to int
        self.summary_counts_df = pd.concat([exp_counts, rxn_counts],axis=1)
        # # Reindex so the order is the same as the types, so plots will be from least -> sequenced
        # temp = summary_counts_df.reindex(types)
        # temp.index.name = "Experiment Type"
        # # Add in the colours and index as column
        # summary_counts_df = temp.reset_index()

        # Identify the expt_types present, create df for each and add df to the dict
        expt_df = { metadata_dict[key].expt_type : pd.DataFrame for key in metadata_dict }
        for expt_type in expt_df.keys():
            #Concatenate data from the same expt_types into the dataframe dict
            expt_df[expt_type] = pd.concat(metadata_dict[key].df for key in metadata_dict if metadata_dict[key].expt_type == expt_type )
            # Add instance attribute for each expt_type
            setattr(self, expt_type.lower() + "_df", expt_df[expt_type])
            # self.expt_type = expt_df[expt_type]

        #Create joins dict according to experiment types present
        joins = {}
        if "sWGA" in expt_df and "PCR" in expt_df :
            joins["sWGA and PCR"] = {"joining": ["sWGA", "PCR"],
                                "left_df": expt_df["sWGA"], 
                                "right_df" : expt_df["PCR"],
                                "on" : "swga_identifier", 
                                "cols" : [ 'sample_id', 'extraction_id'],
                                "suffixes" : ["_sWGA", "_PCR"]
                                } 
        if "PCR" in expt_df and "seqlib" in expt_df :
            joins["PCR and seqlib"] = {"joining": ["PCR", "seqlib"],
                                "left_df":  expt_df["PCR"], 
                                "right_df" :  expt_df["seqlib"], 
                                "on" : "pcr_identifier", 
                                "cols" : [ 'sample_id', 'extraction_id'],
                                "suffixes" : ["_PCR", "_seqlib"]
                                }
        
        print(f"Checking for data validity and merging dataframes for:")
        #Cycle through all of the joins required based on the data present
        for count,join in enumerate(joins):
            #Load the current join from the dict
            join_dict=joins[join]
            print(f"   {join_dict['joining'][0]} and {join_dict['joining'][1]}")
            print("   ------------------")

            #Join the two df together
            data_df = pd.merge(left=join_dict['left_df'],right=join_dict['right_df'],how='outer', on=join_dict['on'], 
                               suffixes=join_dict['suffixes'], indicator=True)
            #Above join appends suffix to column names so create correct list of names
            key_cols = [item + suffix for item in join_dict['cols'] for suffix in join_dict['suffixes'] ]
            expt_id_cols = [ "expt_id" + suffix for suffix in join_dict['suffixes'] ]
            #Combine for user feedback
            show_cols = expt_id_cols + key_cols
            
            #Create df with unmatched records from the right
            # NOT left as this would highlight all that have not been completed / advanced i.e. sWGA performed, but not PCR
            missing_records_df = data_df[data_df['_merge'] == 'right_only']

            # Ensure that only empty sWGA entries are mismatched?
            if join == "sWGA and PCR":
                missing_records_df = missing_records_df[missing_records_df['swga_identifier'].str.lower() != 'no swga']

            # Give user feedback
            if len(missing_records_df) > 0 :
                print(f"   WARNING: {join_dict['joining'][0]} data missing (present in {join_dict['joining'][1]} dataframe)")
                print(missing_records_df[show_cols].to_string(index=False))
                print("")

            #Create df with matched records
            matched_df = data_df[data_df['_merge'] == 'both' ]
            #Identify any mismatched records for the key columns
            for c in join_dict['cols']:
                #Pull out the two dataseries to compare
                col1 = matched_df[f"{c}{join_dict['suffixes'][0]}"]
                col2 = matched_df[f"{c}{join_dict['suffixes'][1]}"]
                #Identify all that don't match
                mismatches_df = matched_df.loc[(col1 != col2) ] 
                #Feedback to user
                if mismatches_df.shape[0] > 0:
                    print(f"   WARNING: Mismatches identified for {c}")
                    print(f"   {mismatches_df[show_cols].to_string(index=False)}")
                    print("")

            #Recreat and merge the dataframes together            
            if count == 0:
                allmetadata_df = pd.merge(left=join_dict['left_df'],right=join_dict['right_df'], 
                                          how="outer",on=join_dict['on'], suffixes=(join_dict['suffixes']))
            else:
                allmetadata_df = pd.merge(left=allmetadata_df,right=join_dict['right_df'],
                                          how="outer",on=join_dict['on'], suffixes=(join_dict['suffixes']))
            print("   Done")
            print("")

        # Fields are essentially duplicated through merging and appended with a suffix e.g. _pcr
        # These need to be collapsed so that a single column captures the details needed
        field_prefixes = ['sample_id' ]
        for field_prefix in field_prefixes:
            # Identify all the fields
            repeat_cols = [col for col in allmetadata_df.columns if col.startswith(field_prefix)]
            # Stack all entries for columns, then take the first entry (not null) of each group.
            # Reindex in case all columns have an empty value, which should never happen, but better to be safe
            allmetadata_df["interim"] =allmetadata_df[repeat_cols].stack().groupby(level=0).first().reindex(allmetadata_df.index)
            #Remove all repeat columns
            allmetadata_df.drop(columns=repeat_cols, inplace=True)
            #Rename interim to original
            allmetadata_df.rename(columns={'interim' :field_prefix}, inplace=True)

        #Create an instance attribute
        self.allmetadata_df = allmetadata_df

        #Fill in the nan values so the aggregation works
        allmetadata_df = allmetadata_df.fillna('None')
        print("Done")
        print("="*80)
        
        # Not sure this is going to be needed anymore as dashboard will show everything:::

        # print("Summarising rxn performed:")
        # Group and aggregate the df to give a list of all experiments performed on each sample 
        # print(expt_df["PCR"])
        # print(self.allmetadata_df.columns)
        # cols_to_retain = ['sample_id', 'extraction_id', 'swga_identifier_sWGA', 'expt_assay', 'pcr_identifier_PCR',
        #                   'seqlib_identifier']
        # self.agg_experiments_df = allmetadata_df[cols_to_retain].groupby(['sample_id', 'expt_assay']).agg(list).reset_index()
        # identifier_cols = [col for col in self.agg_experiments_df.columns if 'identifier' in col]

        # for col in identifier_cols:
        #     value = self._count_non_none_entries_in_dfcolumn(self.agg_experiments_df, col)
        #     name = col.replace("_identifier","")
        #     print(f"   {name}: {value}")
        # print("Done")
        # print("="*80)

        #Optionally export the aggregate data
        if output_folder:
            print(f"Outputting aggregate data to folder: {output_folder.name}")
            
            #Aggregate
            agg_fn = "aggregate_metadata.csv"
            agg_path = output_folder / agg_fn
            self.agg_experiments_df.to_csv(agg_path, index=False)  
            
            print("Done")
            print("="*80)


    def _count_non_none_entries_in_dfcolumn (self, df, column):
        '''
        Function counts the number of non none entries in a column of a dataframe
        '''
        
        return len([item for item in list(chain.from_iterable(df[f"{column}"])) if not item=="None"]) 
    
    def _check_duplicate_entries(self, dt : dict, attribute : str) -> list :
        """Checks for duplicate entries for a defined key in a dictionary.

        Args:
            dt: A populated dictionary.
            attribute: attribute of the object in dt to look for duplicates in

        Returns:
            A list of values that have duplicate entries
        """
        
        # Dictionary to store counts of attribute
        value_counts = {}  

        #For each entry, try to get the key and add to counts
        for _, object in dt.items():
            value = getattr(object, attribute)
            if value:
                if value in value_counts:
                    value_counts[value] += 1
                else:
                    value_counts[value] = 1

        return [k for k,v in value_counts.items() if v > 1]
    
class SampleDataSchema:
    SAMPLEID = "Sample ID"
    DATE = "Date Collected"
    PARASITAEMIA = "Parasitaemia (p/ul)"
    LOCATION = "Province"
    MONTH = "Month"
    YEAR = "Year"

class ExpDataSchema:
    SAMPLEID = "sample_id",
    EXPT_TYPE= "expt_type"

class SampleMetadataParser:
    """
    Extract sample metadata from a single csv file.

    """

    def __init__(self, sample_metadata_fn : Path):
        # load the data from the CSV file
        data = pd.read_csv(
            sample_metadata_fn,
            dtype={
                SampleDataSchema.SAMPLEID: str,
                SampleDataSchema.LOCATION: str,
                SampleDataSchema.PARASITAEMIA: int,
            },
            parse_dates=[SampleDataSchema.DATE],
        )
        data[SampleDataSchema.YEAR] = data[SampleDataSchema.DATE].dt.year.astype(str)
        data[SampleDataSchema.MONTH] = data[SampleDataSchema.DATE].dt.month.astype(str)
        self.df = data
    
class SequencingMetadataParser:
    """
    Extract sequencing data from one or more csv files.

    """

    def __init__(self, seqdata_folder : Path):
        # Identify the files
        print("Searching for bam_flagstats file(s)")
        bamfiles=identify_files_by_search(seqdata_folder, Regex_patterns.SEQDATA_BAMSTATS_CSV)
        print("Searching for bedcov file(s)")
        bedcovfiles=identify_files_by_search(seqdata_folder, Regex_patterns.SEQDATA_BEDCOV_CSV)

        # Extract data and concatenate
        temp1 = pd.DataFrame()
        for file in bamfiles :
            data = pd.read_csv(file)
            temp1 = pd.concat([temp1, data], ignore_index=True)
        self.summary_bam = temp1

        temp2 = pd.DataFrame()
        for file in bedcovfiles :
            data = pd.read_csv(file)
            temp2 = pd.concat([temp2, data], ignore_index=True)
        self.summary_bam = temp2

class MergeSampleExpMetadata:
    """
    Merge the sample and experimental metadata into a cohesive dataframe.

    """

    def __init__(self, exp_metadata_df: pd.DataFrame, sample_metadata_df : pd.DataFrame):
        """
        Merge and fill in the blanks

        """

        #Combine the dataframes
        comb = pd.merge(left=sample_metadata_df, right= exp_metadata_df, how='outer', 
                 left_on=SampleDataSchema.SAMPLEID,
                 right_on=ExpDataSchema.SAMPLEID
                 )
        
        print(f"{comb.shape[0]} records")
        comb.to_csv("output.csv")
        
