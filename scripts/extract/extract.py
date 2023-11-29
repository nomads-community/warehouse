import re
from pathlib import Path
import pandas as pd

class Error(Exception):
    """Error in format or contents of the data"""
    pass

class ExtractMetadata():
    """
    Extract the experimental and individual rxn metadata from the Excel file into a Pandas dataframe. Requires two inputs:

    expdata_folder - Folder containing standardised csv files exported from individual experimental templates
    expt_id - The id of the experiment e.g. SLMM009

    """
    
    def __init__(self, expdata_folder: str, export_folder: str, expt_id: str):
        """
        Load the data

        """
        self.expdata_folder = Path(expdata_folder)
        self.export_folder = Path(export_folder)
        self.tabnames = ["expt_metadata", "rxn_metadata"]
        self.regex_4expid = r'[A-Z]{4}\d{3}'

        #Search for all files or just the specified one
        if not expt_id:
            print("Searching for all experimental files")
            files = self._match_file(".*.xls[x|m]$")
        else:
            self.expt_id = self._check_validexpid(expt_id)
            print(f"Searching for {self.expt_id} experimental file" )
            files = self._match_file(".*" + self.expt_id + ".*.xls[x|m]$", maxfiles=1)
        
        print(f"{len(files)} files identified")
        
        #Identify all the files with the correct sheets
        matched_files = []
        for file in files:
            sheets = pd.ExcelFile(file).sheet_names
            #Check tables are present in file 
            if self.tabnames[0] in sheets and self.tabnames[1] in sheets:
                matched_files.append(file)
        #Export data from each
        if matched_files:
            print(f"{len(matched_files)} valid files identified")
            for file in matched_files:
                print(f"   Found: {file.name}")
                self._export_data(file)
        else:
            print("ERROR: No valid files found.")

    def _match_file(self, searchstring, maxfiles=None):
        """
        Identify all file(s) matching a given search string
        """
        searchstring = re.compile(searchstring)
        matching_files = [ path for path in self.expdata_folder.iterdir()
                          if searchstring.match(path.name) ]
        if maxfiles:
            count = len(matching_files)            
            if count > maxfiles:
                raise Error(f"Expected to find {maxfiles} file, but {count} were found")

        return matching_files
    
    def _identify_exptid(self, filename):
        """
        Extract the experimental ID from a filename
        """
        id_regex = fr'({self.regex_4expid})'
        match = re.search(id_regex, filename.name)
        if match:
            expt_id = match.group(1)
        else:
            raise Error(f"Unable to determine the ExpID from the filename for {filename.name}")
        return expt_id

    def _export_data(self, filename):
        """
        Export experimental metadata
        """
        expt_id = self._identify_exptid(filename)

        for tabname in self.tabnames:
            #Extract data and drop empty rows
            data =  pd.read_excel(filename, sheet_name=tabname)
            data.dropna(how='all', inplace=True)  
            #Export data
            csv_fn = f"{expt_id}_{tabname}.csv"
            csv_fullpath = Path(self.export_folder, csv_fn)
            data.to_csv(csv_fullpath, index=False)
            print(f"      Exported to {csv_fn}")

    def _check_validexpid (self, expt_id):
        """
        Ensure that the supplied ExpID is valid
        """
        id_regex = fr'^{self.regex_4expid}$'
        if not re.match(id_regex,expt_id):
            raise Error(f"{expt_id} is not a valid entry (should be {self.regex_4expid})")
        
        return expt_id