import re
from pathlib import Path
import pandas as pd
from datetime import datetime
from itertools import chain
from lib.exceptions import DataFormatError
from lib.general import identify_files_by_search, create_dict_from_ini, identify_exptid_from_fn, get_nested_key_value, get_dict_entries, filter_dict_by_key, reformat_nested_dict, identify_exptid_from_path, produce_dir
from lib.regex import Regex_patterns
from lib.decorators import singleton

import pretty_errors
pretty_errors.configure(
    stack_depth=1,
    display_locals=1
)

default_ini_folder=Path("./scripts/metadata/dataschemas/")

@singleton           
class ExpDataSchemaFields:
    """
    Pull in all of the dataschema fields 
    """
    def __init__(self):
        ini_files = identify_files_by_search(default_ini_folder, re.compile('exp_.*.ini'))
        
        common_ini = [ path for path in ini_files if "common" in path.name ]
        other_inis =  [ path for path in ini_files if "common" not in path.name ]
            
        common_dict = create_dict_from_ini(common_ini)
        #Need separate lists for different assays ie sWGA etc combined with the common entries
        for ini_file in other_inis:
            # Define library name
            libname=ini_file.name.replace(".ini","_field_labels").replace("exp_","")
            # Pull in nested dict
            libdict = create_dict_from_ini(ini_file)
            #Add common_dict
            libdict.update(common_dict)
            #Reformat to single level dict
            libdict = reformat_nested_dict(libdict,"field","label")
            setattr(self, libname, libdict)

        #Need list for all fields
        self.dataschema_dict = create_dict_from_ini(ini_files)
        
        # Iterate and set attributes
        for dict_key in self.dataschema_dict.keys():
            field_value = get_nested_key_value(self.dataschema_dict, dict_key, "field")
            label_value = get_nested_key_value(self.dataschema_dict, dict_key, "label")
            setattr(self, dict_key.upper(), ( field_value, label_value))
        
class ExpMetadataParser():
    """
    Parse and validate the experimental and individual rxn metadata from an individual Excel spreadsheet.

    """
    
    def __init__(self, file_path: Path, output_folder : Path = None, include_unclassified: bool = False):
        """
        Load and sanity check the metadata

        """
        #Pull in the dynamically created ExpDataSchema
        ExpDataSchema = ExpDataSchemaFields()

        print(f"{file_path.name}")
        self.tabnames = ["expt_metadata", "rxn_metadata"]
        #Store filename
        self.filepath = file_path
        
        #Extract sheetnames
        sheets = pd.ExcelFile(file_path).sheet_names
        #Check both sheets / tabs are present
        if not (self.tabnames[0] in sheets and self.tabnames[1] in sheets):
            raise DataFormatError(f"Missing tabs in {file_path}")
        
        #Load expt data
        self.expt_df = self._extract_excel_data(file_path, self.tabnames[0])
        self.expt_id = self.expt_df[ExpDataSchema.EXP_ID[0]].iloc[0]
        self.expt_date = self.expt_df[ExpDataSchema.EXP_DATE[0]].iloc[0]
        self._check_valid_date_format(self.expt_date)
        self.expt_summary = self.expt_df[ExpDataSchema.EXP_SUMMARY[0]].iloc[0]
        self.expt_type = self.expt_df[ExpDataSchema.EXP_TYPE[0]].iloc[0]
        self.num_rxn = self.expt_df[ExpDataSchema.EXP_RXNS[0]].iloc[0]

        #Check validity of expt data
        self._define_expt_variables()
        self._check_for_columns(self.expt_req_cols, self.expt_df)
        self.expt_rows = self._check_number_rows(1, self.expt_df)
        self._check_expt_id_fn_sheet()

        print("      Experimental metadata passed formatting checks.")

        #Load rxn data
        self.rxn_df = self._extract_excel_data(file_path, self.tabnames[1])

        #Check validity of rxn data
        self._check_for_columns(self.rxn_req_cols, self.rxn_df)
        self.rxn_rows = self._check_number_rows(self.num_rxn, self.rxn_df)
        self._check_entries_unique(self.rxn_unique_cols, self.rxn_df)
        self._check_entries_not_blank(self.rxn_notblank_cols, self.rxn_df)
        if len(self.barcode_pattern) > 0  :
            self.barcodes = self.rxn_df[ExpDataSchema.BARCODE[0]].tolist()
            if include_unclassified:
                self.barcodes.append("unclassified")
            self._check_barcodes_valid()
        print("      Rxn metadata passed formatting checks.")

        print(f"      Merging experimental and rxn data for {self.expt_id}...")
        self.df = pd.merge(self.expt_df, self.rxn_df, on='expt_id', how='inner')

        # Add expt_type back into the rxn dataframe after the merge otherwise there 
        # will be duplicate expt_type cols

        self.rxn_df[ExpDataSchema.EXP_TYPE[0]] = self.rxn_df.get(ExpDataSchema.EXP_TYPE[0], self.expt_type)

        if output_folder is not None:
            produce_dir(output_folder)
            print(f"      Outputting data to folder: {output_folder.name}")
            output_dict = { "expt" : self.expt_df, "rxn" : self.rxn_df }
            for output in output_dict:
                filename = self.expt_id + "_" + output + "_metadata.csv"
                path = output_folder / filename
                output_dict[output].to_csv(path, index=False)
                
        print("Done")

    def _extract_excel_data(self, filename : Path, tabname : str) -> pd.DataFrame:

        """
        Extract data from valid Excel sheets and return a dataframe.

        Args:
            filename(Path): Path object to file
            tabname(str): Excel tab in sheet

        Returns:
            dataframe: Data from Excel tab
        """

        #Extract data and drop empty rows
        data =  pd.read_excel(filename, sheet_name=tabname)
        data.dropna(how='all', inplace=True)

        return data

    def _define_expt_variables(self) -> None:
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
            raise DataFormatError(f"Error experiment type given as {self.expt_type}, expected seqlib, PCR or sWGA.")
        
    def _check_number_rows(self, num_rows : int, df : pd.DataFrame) -> None:
        """
        Check if correct number of rows are present in df

        Args:
            num_rows(int): Number of rows expected
            df(dataframe): dataframe to assess

        """
        found_rows = df.shape[0]
        if found_rows != num_rows:
            print(f"WARNING: Expected {num_rows} rows, but found {found_rows}!")
            # raise MetadataFormatError(f"Expected {num_rows} rows, but found {found_rows}!")

    def _check_for_columns(self, columns : list, df : pd.DataFrame) -> None:
        """
        Check the correct columns are present

        Args:
            columns(list): List of column names
            df(dataframe): dataframe to assess
        """
        for c in columns:
            if c not in df:
                raise DataFormatError(f"Metadata must contain column called {c}!")

    def _check_entries_unique(self, columns : list, df : pd.DataFrame) -> None :
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
                raise DataFormatError(f"Error in barcode name for {barcode}. To be valid, must match this regexp: {self.barcode_pattern}.")

    def _check_valid_date_format(self, date: str, format: str="%Y-%m-%d") -> None:
        """ Check that a `date` adheres to a given `format` """
        try:
            datetime.strptime(date, format)
        except ValueError:
            raise DataFormatError(f"Date {date} does not adhere to expected format: {format}.")
    
    def _check_entries_not_blank(self, columns : list, df : pd.DataFrame) -> None:
        """
        Check that all entries in these columns are not blank

        Args:
            columns
            df (dataframe)
        """
        
        for c in columns:
            df_filtered = df[df[c].isnull()]
            if df_filtered.shape[0] >0 :
                raise DataFormatError(f"Column {c} contains empty data for {self.expt_id}:\n{df_filtered}")

    def _check_expt_id_fn_sheet(self) -> None:
        """
        Check that the expt_id in the filename is the same as the expt_id given in the spreadsheet
        """
        filename_expt_id = identify_exptid_from_fn(self.filepath)

        if not filename_expt_id == self.expt_id:
            raise DataFormatError(f"Exp ID from filename ({filename_expt_id}) and spreadsheet tab ({self.expt_id}) do NOT match")
    
class ExpMetadataMerge():
    """
    Extract metadata from multiple files, merge into a coherent dataframe, and optionally export the data
    """

    def __init__(self, filepaths, output_folder : Path = None):
        #Extract each file as an object into a dictionary 
        expdata_dict = { identify_exptid_from_fn(filepath) : ExpMetadataParser(filepath, output_folder=output_folder) for filepath in filepaths }
        print("="*80)
        
        #Check that there aren't duplicate experiment IDs 
        dupes = self._check_duplicate_entries(expdata_dict, "expt_id")
        if dupes :
            raise ValueError(f"{len(dupes)} duplicate expt_id identfied: {dupes}")

        #Concatenate all the exp level data into a df
        self.expts_df = pd.concat(expdata_dict[key].expt_df for key in expdata_dict )
        #Concatenate all the rxn level data into a df
        self.rxns_df = pd.concat(expdata_dict[key].rxn_df for key in expdata_dict )

        # Identify the expt_types present and create an empty df for each
        expt_df_dict = { expdata_dict[key].expt_type : pd.DataFrame for key in expdata_dict }
        #Create attribute of expt_types for knowing columns generated
        self.expt_types = list(expt_df_dict.keys())

        # Populate df with the appropriate entries and define the 
        for expt_type in expt_df_dict.keys():
            #Concatenate data from the same expt_types into the dataframe dict
            expt_df_dict[expt_type] = pd.concat(expdata_dict[key].df for key in expdata_dict if expdata_dict[key].expt_type == expt_type )
            # Add instance attribute for each expt_type to self
            setattr(self, expt_type.lower() + "_df", expt_df_dict[expt_type])
        
        #Pull in the dynamically created ExpDataSchema as an object
        ExpDataSchema = ExpDataSchemaFields()
        self.DataSchema = ExpDataSchema
                
        #Provide for a case where only a single expt type is present
        if len(self.expt_types) == 1:
            print(f"Only a single expt type ({expt_type}) identified")
            alldata_df = expt_df_dict[expt_type]
        else:
            #Create joins dict according to experiment types present
            joins = {}
            if "sWGA" in expt_df_dict and "PCR" in expt_df_dict :
                joins["sWGA and PCR"] = {"joining": ["sWGA", "PCR"],
                                    "left_df": expt_df_dict["sWGA"],
                                    "right_df" : expt_df_dict["PCR"],
                                    "on" : ExpDataSchema.SWGA_IDENTIFIER[0],
                                    "cols" : [ ExpDataSchema.SAMPLE_ID[0], 
                                              ExpDataSchema.EXTRACTION_ID[0]
                                              ],
                                    "suffixes" : ["_sWGA", "_PCR"]
                                    }
            if "PCR" in expt_df_dict and "seqlib" in expt_df_dict :
                joins["PCR and seqlib"] = {"joining": ["PCR", "seqlib"],
                                    "left_df":  expt_df_dict["PCR"],
                                    "right_df" :  expt_df_dict["seqlib"],
                                    "on" : ExpDataSchema.PCR_IDENTIFIER[0],
                                    "cols" : [ ExpDataSchema.SAMPLE_ID[0], 
                                              ExpDataSchema.EXTRACTION_ID[0]
                                              ],
                                    "suffixes" : ["_PCR", "_seqlib"]
                                    }
            
            print("Checking for data validity and merging dataframes for:")

            #Cycle through all of the joins required based on the data present. Enumerate from 1
            for count,join in enumerate(joins, start=1):
                #Load the current join from the dict
                join_dict=joins[join]
                print(f"   {join_dict['joining'][0]} and {join_dict['joining'][1]}")

                #Join the two df together
                data_df = pd.merge(left=join_dict['left_df'],
                                   right=join_dict['right_df'],
                                   how='outer', 
                                   on=join_dict['on'],
                                   suffixes=join_dict['suffixes'], 
                                   indicator=True)
                
                #Create df with unmatched records from the right
                # NOT left as this would highlight all that have not been completed / advanced i.e. sWGA performed, but not PCR
                missing_records_df = data_df[data_df['_merge'] == 'right_only']

                # Identify names of key columns for reporting back to user and to check for mismatches
                # Above join appends suffix to column names so create correct list of names
                key_cols = [item + suffix for item in join_dict['cols'] for suffix in join_dict['suffixes']]
                expt_id_cols = [ ExpDataSchema.EXP_ID[0] + suffix for suffix in join_dict['suffixes'] ]
                
                #Combine for user feedback and include the join column for quick referencing in spreadsheet
                show_cols = [join_dict['on']] + expt_id_cols + key_cols

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

                #To ensure that all columns have the correct suffix, you need to rejoin the columns with or wthout
                # suffixes depending on whether it is the first (right hand df has no suffix) or last join (both given suffixes)
                if count < len(joins):
                    # Another df to add so leave common fields without a suffix
                    alldata_df = pd.merge(left=join_dict['left_df'],
                                          right=join_dict['right_df'],
                                          how="outer",
                                          on=join_dict['on'],
                                          suffixes=([join_dict['suffixes'][0], None]))
                else:
                    # Last df being merged so give all a suffix
                    alldata_df = pd.merge(left=alldata_df,
                                          right=join_dict['right_df'],
                                          how="outer",
                                          on=join_dict['on'],
                                          suffixes=(join_dict['suffixes']))
            
            #Collapse columns where multiple entries exist
            alldata_df = self.collapse_columns(alldata_df, [ ExpDataSchema.SAMPLE_ID[0] ])

            #Remove the expt_type fields as they are not informative in a merged df
            dropcols = [col for col in alldata_df.columns if col.startswith(ExpDataSchema.EXP_TYPE[0])]
            alldata_df.drop(dropcols, axis=1, inplace=True)

            #Fill in the nan values
            alldata_df = alldata_df.fillna('None')
            
            print("Summarising rxn performed")
            # Group and aggregate the df to give a list of all experiments performed on each sample 
            col_roots = [ExpDataSchema.SAMPLE_ID[0],
                         ExpDataSchema.EXTRACTION_ID[0],
                         ExpDataSchema.PCR_ASSAY[0],
                         ExpDataSchema.SWGA_IDENTIFIER[0],
                         ExpDataSchema.PCR_IDENTIFIER[0],
                         ExpDataSchema.SEQLIB_IDENTIFIER[0],
                         ]
            collapsed_df = self.collapse_columns(alldata_df, col_roots)
            self.exp_summary_df = collapsed_df[col_roots].groupby([ExpDataSchema.SAMPLE_ID[0],
                                                                   ExpDataSchema.PCR_ASSAY[0]]
                                                                   ).agg(list).reset_index()

        #Create an instance attribute
        self.all_df = alldata_df
        print("Done")
        print("="*80)

        #Optionally export the aggregate data
        if output_folder:
            print(f"Outputting all data to folder: {output_folder.name}")
            
            self._export_df_to_csv(self.all_df, output_folder, "experimental_data_all.csv")
            self._export_df_to_csv(self.exp_summary_df, output_folder, "experimental_data_summary.csv")

            print("Done")
            print("="*80)
        
    def _export_df_to_csv(self, df : pd.DataFrame, folder: Path, filename: str) -> None:
        """
        Export a df to a csv file
        Args:
            df (pd.DataFrame): The pandas DataFrame to export.
            folder (Path): Path object folder where the CSV will be saved.
            filename (str):  .csv filename to be created.

        Returns:    
            None
        """
        
        path = folder / filename
        df.to_csv(path, index=False)

    def collapse_columns(self, df : pd.DataFrame, field_roots : list) -> pd.DataFrame:
        """
        Merging dataframes creates duplicated fields that only differ by suffix e.g. _pcr. 
        These need to be collapsed so that a single column captures the details needed.

        Args:
            df (pd.DataFrame): The pandas DataFrame to collapse columns in.
            field_roots (list): List of root fieldnames e.g. sample_id

        Returns:    
            df (pd.DataFrame): The pandas DataFrame with the duplicate columns dropped.     
        """

        for root in field_roots:
            # Identify all the fields
            repeat_cols = [col for col in df.columns if col.startswith(root)]
            # Stack all entries for columns, then take the first entry (not null) of each group.
            # Reindex in case all columns have an empty value, which should never happen, but better to be safe
            df["interim"] = df[repeat_cols].stack().groupby(level=0).first().reindex(df.index)
            #Remove all repeat columns
            df.drop(columns=repeat_cols, inplace=True)
            #Rename interim to original
            df.rename(columns={'interim' :root}, inplace=True)

        return df

    def _count_non_none_entries_in_dfcolumn (self, df : pd.DataFrame, column : str) -> int:
        """
        Function counts the number of non none entries in a column of a dataframe
        Args:
            df (pd.DataFrame): The pandas DataFrame to export.
            column (str): Name of the column to assess
        
        Returns:
            int : Count of entries in the column that are not None.
        """
        
        return len([item for item in list(chain.from_iterable(df[f"{column}"])) if not item=="None"]) 
    
    def _check_duplicate_entries(self, dt : dict, attribute : str) -> list :
        """
        Checks for duplicate entries for a defined key in a dictionary.

        Args:
            dt: A populated dictionary.
            attribute: attribute of the object in dt to look for duplicates in

        Returns:
            A list of values that have duplicate entries
        """
        
        # Dictionary to store counts of attribute
        values_dict = {}
        
        #For each entry, try to get the key and add to counts
        for key, object in dt.items():
            #Pull out the value
            value = getattr(object, attribute)
            if value:
                if key in values_dict:
                    values_dict[value] += 1
                else:
                    values_dict[value] = 1

        return [k for k,v in values_dict.items() if v > 1]

@singleton           
class SampleDataSchemaFields:
    """
    Pull in all of the dataschema fields
    """
    def __init__(self, csv_path : Path):
        #Get a list of all ini paths
        ini_files = identify_files_by_search(csv_path.parent, re.compile('.*.ini'))
        
        if len(ini_files) > 1:
            print(f"Multiple .ini files found, using first one: {ini_files[0]}")
        self.dataschema_dict = create_dict_from_ini(ini_files[0])
        
        #Create simple dict of field and labels
        self.field_labels = reformat_nested_dict(self.dataschema_dict, "field", "label")

        # Iterate and set attributes
        for dict_key in self.dataschema_dict.keys():
            field_value = get_nested_key_value(self.dataschema_dict, dict_key, "field")
            label_value = get_nested_key_value(self.dataschema_dict, dict_key, "label")
            setattr(self, dict_key.upper(), ( field_value, label_value))
        
        # Identify all with datatype entries
        self.dtypes = get_dict_entries(self.dataschema_dict,"field", "datatype", "date")
        # Identify all that ARE dates
        self.datefields = get_dict_entries(self.dataschema_dict, "field", "datatype", "date", True)
        # Identify all dates that have a defined format
        self.dateformats = get_dict_entries(self.dataschema_dict, "field", "dateformat")

class SampleMetadataParser():
    """
    Extract sample metadata from a single csv file, define fieldnames and labels,
    and determine experimental status of each sample (if passed data).

    """

    def __init__(self, sample_csv_path : Path, rxn_df : pd.DataFrame = None):
        
        #Load dataschema for sample set and save as attribute
        SampleDataSchema = SampleDataSchemaFields(sample_csv_path)
        self.DataSchema = SampleDataSchema
        # self.dataschema_dict = SampleDataSchema.dataschema_dict
        
        ExpDataSchema = ExpDataSchemaFields()

        # load the data from the CSV file
        df = pd.read_csv(
                sample_csv_path,
                dtype=SampleDataSchema.dtypes
            )
        
        #Ensure dates are correctly formatted
        for datefield in SampleDataSchema.datefields:
            f = SampleDataSchema.dateformats.get(datefield, "")
            if f:
                df[datefield] = pd.to_datetime(df[datefield], format=f)
            else:
                df[datefield] = pd.to_datetime(df[datefield])
            
            #Check if dates parsed correctly
            if not pd.api.types.is_datetime64_dtype(df[datefield]):
                raise DataFormatError(f"Date errors in field / column: {datefield}")
        
        # Determine the point each sample has got through to in testing
        if rxn_df is not None :
            #Define column name to reference and add to dict
            # SampleDataSchema.STATUS
            # status = "Status"
            # self.dataschema_dict.setdefault("STATUS", {"field": status, "datatype": "str", "label": "Sample Test Status"})

            # Create status column and fill with not tested
            df[SampleDataSchema.STATUS[0]] = df.get(SampleDataSchema.STATUS[0], default=ExpThroughputDataScheme.EXP_TYPES[0])
            
            # Define what is present
            types_present = rxn_df[ExpDataSchema.EXP_TYPE[0]].unique()
            for type in ExpThroughputDataScheme.EXP_TYPES: # Ensure order is followed
                if type in types_present :
                    #Get a list of samples that have the same matching expt_type
                    samplelist=rxn_df[rxn_df[ExpDataSchema.EXP_TYPE[0]] == type][ExpDataSchema.SAMPLE_ID[0]].tolist()
                    #Enter result into df overwriting previous entries
                    df.loc[df['sample_id'].isin(samplelist), SampleDataSchema.STATUS[0]] = type
        
        # Define attributes
        self.df = df
        
@singleton           
class SeqDataSchemaFields:
    """
    Pull in all of the dataschema fields
    """
    def __init__(self, ):
        ini_files = identify_files_by_search(default_ini_folder, re.compile('seq_nomadic.ini'))
        self.dataschema_dict = create_dict_from_ini(ini_files)
        
        self.field_labels = reformat_nested_dict(self.dataschema_dict, "field","label")
        # Iterate and set attributes as a tuple with the field_name first and human label second
        for dict_key in self.dataschema_dict.keys():
            field_value = get_nested_key_value(self.dataschema_dict, dict_key, "field")
            label_value = get_nested_key_value(self.dataschema_dict, dict_key, "label")
            setattr(self, dict_key.upper(), ( field_value, label_value))

        #Define list of fields for mapped list
        self.MAPPED_LIST = [ value["field"] for value in self.dataschema_dict.values() if "mapping_list" in value ]

class SequencingMetadataParser():
    """
    Extract sequencing data from one or more csv files.

    """

    def __init__(self, seqdata_folder : Path, exp_data : object):
        #Load dataschema for sample set and save as an object attribute
        SeqDataSchema = SeqDataSchemaFields()
        self.DataSchema = SeqDataSchema
        
        #Define the expdataschema object
        ExpDataSchema = exp_data.DataSchema
        
        #Filter dict to key fields to match on
        key_fields = filter_dict_by_key(ExpDataSchema.dataschema_dict,[ "EXP_ID", "SAMPLE_ID", "EXTRACTIONID", "BARCODE"])
        #Simplify dict to a list of keys (fieldnames) 
        key_fields = list(reformat_nested_dict(key_fields, "field", "label").keys())
        
        #Need to match the sequence data outputs to the exp.rxn_df to merge correctly
        # Make a deep copy of the df
        match_df = exp_data.rxns_df.copy()
        #Trim to relevent columns
        match_df = match_df[key_fields]
        
        def extract_add_concat(files : list[Path], exp_seq_df : pd.DataFrame) -> pd.DataFrame:
            """
            Function to extract, modify and concatenate multiple csv files of the same type into a df.
            Then merge the df to experimental data to add additional required details.

            Args:
                files list(Path):  List of Path names
                exp_seq_df (df):   Experimental data Dataframe to match to csv 
            """
            #Create empty df
            temp = pd.DataFrame()
            
            # Extract data, add in experiment ID and concatenate all data
            for file in files:
                expid = identify_exptid_from_path(file)
                data = pd.read_csv(file)
                data[ExpDataSchema.EXP_ID[0]] = expid
                temp = pd.concat([temp, data], ignore_index=True)
            
            # Merge to add in additional cols from the exp_data ie sample_id and extraction_id
            merged = pd.merge(left=temp, right=exp_seq_df, 
                                left_on=[ SeqDataSchema.EXP_ID[0], SeqDataSchema.BARCODE[0]], 
                                right_on=[ExpDataSchema.EXP_ID[0], ExpDataSchema.BARCODE[0]], 
                                how="inner")
            return merged
        
        print("   Searching for bam_flagstats file(s)")
        bamfiles=identify_files_by_search(seqdata_folder, Regex_patterns.SEQDATA_BAMSTATS_CSV, recursive=True)
        self.summary_bam = extract_add_concat(bamfiles, match_df)
        
        print("   Searching for bedcov file(s)")
        bedcovfiles=identify_files_by_search(seqdata_folder, Regex_patterns.SEQDATA_BEDCOV_CSV, recursive=True)
        self.summary_bedcov = extract_add_concat(bedcovfiles, match_df)

@singleton
class CombinedData:
    """
    Merge all data sources
    """
    def __init__(self, exp_data, sequence_data, sample_data):
        
        ExpDataSchema = exp_data.DataSchema
        SeqDataSchema = sequence_data.DataSchema
        SampleDataSchema = sample_data.DataSchema
        
        alldata_df = pd.merge(exp_data.all_df, sequence_data.summary_bam, 
                            left_on=[ExpDataSchema.BARCODE[0], f"{ExpDataSchema.EXP_ID[0]}_seqlib", ExpDataSchema.SAMPLE_ID[0]],
                            right_on=[SeqDataSchema.BARCODE[0], SeqDataSchema.EXP_ID[0], SeqDataSchema.SAMPLE_ID[0]],
                            how ="outer")
        
        # Add in the sample data to above merge
        alldata_df = pd.merge(alldata_df, sample_data.df, 
                            left_on=[ExpDataSchema.SAMPLE_ID[0]],
                            right_on=[SampleDataSchema.SAMPLE_ID[0]],
                            how="outer")
        
        #Define df as an attribute
        self.df = alldata_df
        #define list of refs for dropdowns
        self.datasources_dict = {"sWGA": "Experimental (sWGA)",
                    "PCR": "Experimental (PCR)",
                    "seqlib": "Experimental (seqlib)",
                    "sample": "Sample information",
                    "seqdata": "Sequence Analysis (nomadic)"
                    }
        
        #List of variable names for each data source
        self.datasource_fields = {"sWGA": ExpDataSchema.sWGA_field_labels,
                        "PCR": ExpDataSchema.PCR_field_labels,
                        "seqlib": ExpDataSchema.seqlib_field_labels,
                        "sample": SampleDataSchema.field_labels,
                        "seqdata": SeqDataSchema.field_labels,
        }
        
        #List of all field label combos
        self.dataschema_dict = ExpDataSchema.dataschema_dict | SampleDataSchema.dataschema_dict | SeqDataSchema.dataschema_dict
        
        #Collapse into a list of all field and labels for any translations
        all_field_labels = {}
        for dict_value in self.datasource_fields.values():
                all_field_labels = all_field_labels | dict_value
        self.all_field_labels = all_field_labels
        
class ExpThroughputDataScheme:
    #### Definitions for making the summary throughput calculations #####
    SAMPLES= "experiments"
    EXPERIMENTS= "reactions"
    REACTIONS= "samples"
    # Define as a tuple so it is ordered and immutable
    EXP_TYPES = ('Not tested', 'sWGA','PCR','seqlib')
    