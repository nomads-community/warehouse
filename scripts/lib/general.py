import re
from pathlib import Path

# regex for a NOMADS template file match
id_regex = '(SW|PC|SL)[a-zA-Z]{2}[0-9]{3}.*.xlsx'

def identify_exptid_from_fn(filename: Path):
    """
    Extract the experimental ID from a filename

    Args:
    filename (Path): path to the file

    Returns:
        expt_id: the extracted experiment id or None if not found
    """

    try:
        match = re.search(id_regex, filename.name)
        expt_id = match.group(0)
        return expt_id
    
    except StopIteration:
        print(f"Unable to determine the ExpID from the filename for {filename.name}")
        return None

def identify_nomads_files(metadata_folder: Path, expt_id: str = None):

    """
    Identify if there is a file containing the supplied ExpID or files that are NOMADS 
    named templates"

    Args:
    metadata_folder (Path): path to the metadata folder.
    expt_id (str): The experiment ID to search for (optional)

    Returns:
        Path: The path to the matching file(s), or None if not found.
    """

    openfile_pattern = re.compile(r"^[/.|~]") 

    if expt_id is not None:
        search_pattern = re.compile(f".*{expt_id}_.*.xlsx")
        targets = 1
    else:
        search_pattern = re.compile(id_regex)
        targets = None
    
    try:
        #List all  entries matching the searchpattern
        matches = [f for f in metadata_folder.iterdir() if search_pattern.search(f.name)]
        
        #List all open Excel files
        openfiles = [f for f in matches if openfile_pattern.findall(f.name)]

        #Ensure there are non open files
        if len(openfiles) > 0:
            raise ValueError(f"{len(openfiles)} open Excel files identified. Please close and run again:")

        #Feedback to user what has been found
        if targets != 1:
            print(f"Found {len(matches)} matching files")
            return matches 
        
        if len(matches) > 1:
            raise ValueError(f"Multiple matches found: {matches}")
        
        if len(matches) == 0:
            raise ValueError(f"No matching files found.")
        
        match = matches[0]
        print(f"Found: {match.name}")
        return match

    except FileNotFoundError:
        print(f"Error: Folder '{folder}' not found.")

    except StopIteration:
        print("No matching file found")
        return None

    except ValueError as error_msg:
        print(str(error_msg))
        raise