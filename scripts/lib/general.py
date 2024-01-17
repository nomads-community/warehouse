import re
from pathlib import Path
from .exceptions import MetadataFormatError

class identify_exptid_from_fn(MetadataFormatError):
    """
    Extract the experimental ID from a filename
    """
    def __init__(self, filename: Path):
        id_regex = '(SW|PC|SL)[a-zA-Z]{2}\d{3}'
        match = re.search(id_regex, filename.name)
        if match: 
            self.expt_id = match.group(0)
        else:
            raise MetadataFormatError(f"Unable to determine the ExpID from the filename for {filename.name}")
        

class identify_fn_from_exptid(MetadataFormatError):

    """
    Identify if there is a file containing the ExpID
    """

    def __init__(self, metadata_folder: Path, expt_id: str = False ):
        searchstring = re.compile(f".*_{expt_id}_.*.xlsx")
        matching_filepaths = [ path for path in metadata_folder.iterdir()
                           if searchstring.match(path.name) ]
        
        count = len(matching_filepaths)            
        if count != 1:
            raise MetadataFormatError(f"Expected to find 1 file, but {count} were found")
        else:
            self.match_path = matching_filepaths[0]
            print(f"   Found: {self.match_path.name}")