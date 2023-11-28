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
        self.expt_id = expt_id
        self.tabnames = ["expt_metadata", "rxn_metadata"]

        #Search for all files or just the specified one
        if not self.expt_id:
            print("Searching for all experimental files")
            searchstring = re.compile(".*.xls[x|m]$")
            files = [ path for path in self.expdata_folder.iterdir()
                          if searchstring.match(path.name) ]
            print(f"{len(files)} files identified")
        else:
            print(f"Searching for {expt_id} experimental file" )
            #Identify expt file
            files = [ self._match_file(".*" + self.expt_id + ".*.xls[x|m]$") ]
        
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

    def _match_file(self, searchstring):

        """
        Identify if there is a matching file for the given expt_id
        """
        searchstring = re.compile(searchstring)
        matching_files = [ path for path in self.expdata_folder.iterdir()
                          if searchstring.match(path.name) ]
        
        count = len(matching_files)            
        if count != 1:
            raise Error(f"Expected to find 1 file, but {count} were found")
        else:
            match_path = matching_files[0]

        return match_path
    
    def _identify_exptid(self, filename):
        """
        Extract the experimental ID from a filename
        """
        pattern = r'_([A-Z]{4}\d{3})'
        match = re.search(pattern, filename.name)
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
            #Extract data
            data =  pd.read_excel(filename, sheet_name=tabname)
            #Export data
            csv_fn = f"{expt_id}_{tabname}.csv"
            csv_fullpath = Path(self.export_folder, csv_fn)
            data.to_csv(csv_fullpath, index=False)
            print(f"      Exported to {csv_fn}")