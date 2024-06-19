import re, os
from pathlib import Path
from .exceptions import DataFormatError

class Regex_patterns():
    #Identifying NOMADS specific files
    SEQDATA_BAMSTATS_CSV=re.compile(r'.*bam_flagstats.*.csv')    
    SEQDATA_BEDCOV_CSV=re.compile(r'.*summary.*bedcov.*.csv')
    NOMADS_EXPID=re.compile(r"(SW|PC|SL)[a-zA-Z]{2}[0-9]{3}")
    NOMADS_EXP_TEMPLATE=re.compile(r"(SW|PC|SL)[a-zA-Z]{2}[0-9]{3}.*.xlsx")

    #Files that are open
    EXCEL_FILES = re.compile(r"^[/.|~]")
    CSV_FILES = re.compile(r"~lock")
    OPENFILES = re.compile("|".join([EXCEL_FILES.pattern, CSV_FILES.pattern]))

def identify_exptid_from_path (path: Path) -> str:
    """
    Extract the experimental ID from a file or folder

    Args:
        path (Path): path to the folder

    Returns:
        expt_id (str): the extracted experiment id or None if not found
    """

    try:
        #First try with the path name
        match = re.search(Regex_patterns.NOMADS_EXPID, path.name)
        if match is None:
            #Second try with the full path
            match = re.search(Regex_patterns.NOMADS_EXPID, str(path))
        if match is None:
            raise DataFormatError(f"Unable to identify an ExpID in: {path}")
        
        return match.group(0)
        
    
    except StopIteration:
        # print(f"Unable to identify an ExpID in: {path.name}")
        raise DataFormatError(f"Unable to identify an ExpID in: {path.name}")


def identify_exptid_from_fn(path: Path) -> str:
    """
    Extract the experimental ID from a filename

    Args:
        path (Path): path to the file

    Returns:
        expt_id (str): the extracted experiment id or None if not found
    """

    try:
        match = re.search(Regex_patterns.NOMADS_EXP_TEMPLATE, path.name)
        expt_id = match.group(0)
        return expt_id
    
    except StopIteration:
        print(f"Unable to identify an ExpID in: {path.name}")
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

    #Extract path from the list object
    path = matches[0]
    return path

def _check_no_openfiles_identified(fn_list : list) :
    """
    Identify if there are any files from a list that are currently open"

    Args:
    fn_list (list): List of file paths (pathlib).

    """
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

def identify_all_files (folder : Path):
    """
    Identify all files in a folder"

    Args:
    folder (Path): path to the search folder.
    
    Returns:
        Path: The path to the matching file(s), or None if not found.
    """

    all_files = []
    for entry in folder.iterdir():
        if entry.is_file():
            all_files.append(entry)
        elif entry.is_dir():
        # Recursively search subdirectories
            all_files.extend(identify_all_files(entry))
    return all_files

    
def identify_files_by_search(folder_path: Path, pattern: str):

    """
    Identify all files in a folder that match a search pattern"

    Args:
    folder (Path): path to the search folder.
    pattern (re.pattern): Compiled RE pattern to match filename against
    
    Returns:
        Path: The path to the matching file(s), or None if not found.
    """
    
    try:
        matches = [f for f in identify_all_files(folder_path) if pattern.search(f.name)]
            
        #Check that there are no open files
        _check_no_openfiles_identified(matches)

        #Check there are no duplicate names
        _check_duplicate_names(matches)

        #Esnure there is at least one match
        if len(matches) == 0:
            raise ValueError(f"No matching files found.")
        
        #Feedback to user what has been found
        print(f"Found {len(matches)} matching file(s)")
        return matches 

    except FileNotFoundError:
        print(f"Error: Folder '{folder_path.name}' not found.")

    except StopIteration:
        print("No matching file found")
        return None

    except ValueError as error_msg:
        print(str(error_msg))
        raise




def produce_dir(*args):
    """
    Produce a new directory by concatenating `args`,
    if it does not already exist

    params
        *args: str1, str2, str3 ...
            Comma-separated strings which will
            be combined to produce the directory,
            e.g. str1/str2/str3

    returns
        dir_name: str
            Directory name created from *args.

    """

    # Define directory path
    dir_name = os.path.join(*args)

    # Create if doesn't exist
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
        print(f"   {dir_name} created")

    return dir_name