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
    num_targets = None
    
    if expt_id is not None:
        search_pattern = re.compile(f".*{expt_id}_.*.xlsx")
        num_targets = 1
    else:
        search_pattern = re.compile(id_regex)

    try:
        #Create a list of all subfolders and parent
        folders = [ metadata_folder] + _list_folders_in_dir(metadata_folder)  
        matches = []
        for folder in folders :
            #List all  entries matching the searchpattern and add to list
            new_matches = [f for f in folder.iterdir() if search_pattern.search(f.name)]
            matches.extend(new_matches)

        #List all open Excel files
        openfiles = [f for f in matches if openfile_pattern.findall(f.name)]

        #Ensure there are not any open files
        if openfiles:
            raise ValueError(f"{len(openfiles)} open Excel files identified. Please close and run again:")
        
        #Ensure there are no duplicate filenames
        dupes = _check_duplicate_names(matches)
        if dupes :
            raise ValueError(f"Identical files identified: {dupes}. Please resolve and run again:")
        
        #Esnure there is at least one match
        if len(matches) == 0:
            raise ValueError(f"No matching files found.")
        
        #Feedback to user what has been found
        #For multiple targets:
        if num_targets == None:
            print(f"Found {len(matches)} matching files")
            return matches 
        
        #For defined num of targets 
        if len(matches) == num_targets:
            match = matches[0]
            print(f"Found: {match.name}")
            return match 

        raise ValueError(f"Multiple matches found: {matches}")

    except FileNotFoundError:
        print(f"Error: Folder '{metadata_folder.name}' not found.")

    except StopIteration:
        print("No matching file found")
        return None

    except ValueError as error_msg:
        print(str(error_msg))
        raise

def _list_folders_in_dir(directory: Path) :
    """
    Lists all folders within a given directory using pathlib.
  
    Args:
    directory (Path): path to the directory.
    
    Returns:
    folders (list): pathlib paths to matching folders.
    """
    folders = []
    for entry in Path(directory).iterdir():
        if entry.is_dir():
            folders.append(entry)
    return folders

def _check_duplicate_names(entries):
  """Checks for duplicate names in a list of pathlib entries.

  Args:
      entries: A list of pathlib.Path objects.

  Returns:
      A list of filenames that appear more than once.
  """
  seen_names = set()
  duplicates = []
  for entry in entries:
    filename = entry.name
    if filename in seen_names:
        duplicates.append(filename)
    else:
        seen_names.add(filename)
  return duplicates