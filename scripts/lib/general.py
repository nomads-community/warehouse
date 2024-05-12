import re, os
from pathlib import Path

class Regex_patterns():
    #Identifying NOMADS specific files
    EXPERIMENTALDATA_TEMPLATE = '(SW|PC|SL)[a-zA-Z]{2}[0-9]{3}.*.xlsx'
    SEQDATASUMMARY_CSV='summary.*.csv'
    NOMADS_EXP_TEMPLATE=re.compile(r"(SW|PC|SL)[a-zA-Z]{2}[0-9]{3}.*.xlsx")

    #Files that are open
    EXCEL_FILES = re.compile(r"^[/.|~]")
    CSV_FILES = re.compile(r"~lock")
    OPENFILES = re.compile("|".join([EXCEL_FILES.pattern, CSV_FILES.pattern]))

def identify_exptid_from_fn(filename: Path):
    """
    Extract the experimental ID from a filename

    Args:
    filename (Path): path to the file

    Returns:
        expt_id: the extracted experiment id or None if not found
    """

    try:
        match = re.search(Regex_patterns.EXPERIMENTALDATA_TEMPLATE, filename.name)
        expt_id = match.group(0)
        return expt_id
    
    except StopIteration:
        print(f"Unable to determine the ExpID from the filename for {filename.name}")
        return None

def identify_experiment_file(metadata_folder: Path, expt_id: str = None):
    """
    Identify if there is a file with the ExpID in the list of filenames"

    Args:
    files_list (list): List of file paths.
    expt_id (str): Experiment ID to search for (optional)

    Returns:
        Path: The path to the matching file, or None if not found.
    """
    
    matches = identify_files_by_search(metadata_folder, Regex_patterns.NOMADS_EXP_TEMPLATE)
    search_pattern = re.compile(f".*{expt_id}_.*.xlsx")
    matches = [f for f in matches if search_pattern.search(os.path.basename(f))]
    
    #Esnure there is at least one match
    if len(matches) == 0:
        raise ValueError(f"No matching files found.")
    
    if len(matches) > 1:
        raise ValueError(f"Multiple matches found: {matches}")

    #Feedback to user what has been found
    print(f"Found {len(matches)} file")
    
    #Extract path from the list object
    path = matches[0]
    return path


def _check_no_openfiles_identified(fn_list : list) :

    #List all open files
    openfiles = [f for f in fn_list if Regex_patterns.OPENFILES.match(f.name)]
    #Ensure there are not any open files in the supplied list
    if openfiles:
        raise ValueError(f"{len(openfiles)} open files identified. Please close and run again:")
        
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

def check_file_present (filename: Path) -> bool :
    """
    Checks for the presence of a file using pathlib.
  
    Args:
    directory (Path): path to the file.
    
    Returns:
    Bool: true if file exists, false if not.
    """
    if not filename.exists():
        raise ValueError(f"{filename} does not exist. Exiting...")
    return filename.exists()

def identify_files_by_search(folder_path: Path, pattern: str):

    """
    Identify all files in a folder (plus one level down) based on a search pattern"

    Args:
    folder (Path): path to the search folder.
    pattern (re.pattern): Compiled RE pattern to match filename against
    
    Returns:
        Path: The path to the matching file(s), or None if not found.
    """
    
    try:
        #Create a list of all subfolders and parent
        folders = [ folder_path] + _list_folders_in_dir(folder_path)
        
        matches = []
        for folder in folders :
            #List all  entries matching the searchpattern and add to list
            new_matches = [f for f in folder.iterdir() if pattern.search(f.name)]
            matches.extend(new_matches)
        
        #Check that there are no open files
        _check_no_openfiles_identified(matches)

        #Check there are no duplicate names
        _check_duplicate_names(matches)

        #Esnure there is at least one match
        if len(matches) == 0:
            raise ValueError(f"No matching files found.")
        
        #Feedback to user what has been found
        print(f"Found {len(matches)} matching files")
        return matches 

    except FileNotFoundError:
        print(f"Error: Folder '{folder_path.name}' not found.")

    except StopIteration:
        print("No matching file found")
        return None

    except ValueError as error_msg:
        print(str(error_msg))
        raise

