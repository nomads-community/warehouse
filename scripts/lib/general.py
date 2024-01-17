import re
from pathlib import Path, PurePath
from .exceptions import MetadataFormatError

class identify_exptid_from_fn(MetadataFormatError):
    """
    Extract the experimental ID from a filename
    """
    def __init__(self, filename: str):
        id_regex = '(SW|PC|SL)[a-zA-Z]{2}\d{3}'
        filename=Path(filename)
        match = re.search(id_regex, filename.name)
        if match: 
            self.expt_id = match.group(0)
        else:
            raise MetadataFormatError(f"Unable to determine the ExpID from the filename for {filename.name}")
        

class identify_fn_from_exptid(MetadataFormatError):

    """
    Identify if there is a file containing the ExpID
    """

    def __init__(self, metadata_folder:str, expt_id: str = False ):
        searchstring = re.compile(f".*_{expt_id}_.*.xlsx")
        metadata_folder_path = Path(metadata_folder)
        matching_filepaths = [ path for path in metadata_folder_path.iterdir()
                           if searchstring.match(path.name) ]
        
        count = len(matching_filepaths)            
        if count != 1:
            raise MetadataFormatError(f"Expected to find 1 file, but {count} were found")
        else:
            self.match_path = matching_filepaths[0]
            print(f"   Found: {PurePath(self.match_path).name}")