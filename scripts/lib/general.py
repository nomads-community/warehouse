import re
import os
import configparser
from pathlib import Path
from .exceptions import DataFormatError
from .regex import Regex_patterns

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
        match = re.search(Regex_patterns.NOMADS_EXPID, path.name)
        expt_id = match.group(0)
        return expt_id
    
    except StopIteration:
        print(f"Unable to identify an ExpID in: {path.name}")
        return None

def identify_experiment_file(folder: Path, expt_id: str = None):
    """
    Identify if there is an Excel file with a matching ExpID pattern in the list of filenames"

    Args:
    files_list (list): List of file paths.
    expt_id (str): Experiment ID to search for (optional)

    Returns:
        Path: The path to the matching file, or None if not found.
    """
    print("Searching for all NOMADS template files")
    matches = identify_files_by_search(folder, Regex_patterns.NOMADS_EXP_TEMPLATE, recursive=True)
    # search_pattern = re.compile(f".*{expt_id}_.*.xlsx")

    print(f"Searching for files with {expt_id} in name")
    search_pattern = re.compile(f"{expt_id}")
    matches = [f for f in matches if search_pattern.search(f.name)]
    
    #Esnure there is at least one match
    if len(matches) == 0:
        raise ValueError("No matching files found.")
    
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

def identify_all_files (folder : Path, recursive : bool = False) -> list[Path]:
    """
    Identify all files in a folder / directory

    Args:
    folder (Path): path to the folder
    recursive (Bool): Select whether search should be recursive
    
    Returns:
    list[Path]: List of paths in specified folder, or None if none present.
    """

    all_files = []
    for entry in folder.iterdir():
        if entry.is_file():
            all_files.append(entry)
        elif entry.is_dir():
            if recursive:
                # Recursively search subdirectories
                all_files.extend(identify_all_files(entry, True))
    return all_files
    
def identify_files_by_search(folder_path: Path, pattern: str, recursive : bool = False) -> list[Path]:

    """
    Identify all files in a folder that match a search pattern"

    Args:
    folder (Path): path to the search folder.
    pattern (re.pattern): Compiled RE pattern to match filename against
    recursive (Bool): Select whether search should be recursive
    
    Returns:
        list[Path]: List of paths to the matching file(s), or None if not found.
    """
    
    try:
        matches = [f for f in identify_all_files(folder_path, recursive) if pattern.search(f.name)]
            
        #Check that there are no open files
        _check_no_openfiles_identified(matches)

        #Check there are no duplicate names
        _check_duplicate_names(matches)

        #Esnure there is at least one match
        if len(matches) == 0:
            raise ValueError("No matching files found.")
        
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

def produce_dir(*args) -> str:
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

def create_dict_from_ini(ini_files : Path|list[Path]) -> dict:
    """
    Define data fields from a .ini file

    Args:
        ini_files list[Path]: Path(s) to ini file

    Returns:  
        dict:   dictionary containing all details from ini file(s)
    """
    if isinstance(ini_files, Path):
        # Single entry (convert to list for consistency)
        ini_files = [ini_files]

    # Create an empty dictionary to store data
    field_dict = {}
    
    for ini_file in ini_files :
        config = configparser.ConfigParser()
        config.read(ini_file)
        
        for section, items in config.items():
            for key, value in items.items():
                # Enter the key and value into dict
                field_dict.setdefault(key.upper(), {})[section] = value
    return field_dict   
    
def get_nested_key_value(data_dict : dict, key : str, nested_key : str) -> str|dict:
    """
    Retrieves the label for a given key from the dictionary.

    Args:
        key (str): The key of the field to get values from (uppercase)
        nested_key: The nested key of field to get values from

    Returns:
        str|dict: The value for the nested_key, or None if not found.
    """

    return data_dict.get(key, {}).get(nested_key)           

def filter_nested_dict_by_attribute(nested_dict: dict, attributes : str|list) -> dict:
    """
    Filters a nested dictionary to those containing a specific attribute

    Args:
        nested_dict (dict):   Nested dictionary to filter
        attribute (str|list):    Attribute(s) to search for in the dict values
    
    Returns:
    
    """

    def has_all_attributes(value: dict, attributes : list) -> bool:
        """
        Checks if a dictionary value contains all the attributes in the provided list.

        Args:
            value (dict): The dictionary value to check.
            attributes (list): The list of attributes to search for.

        Returns:
            bool: True if all attributes are found in the value, False otherwise.
        """
        return all(attr in value.keys() for attr in attributes)

    # Single attribute case (convert to list for consistency)
    if isinstance(attributes, str):
        attributes = [attributes]

    # Filter based on all attributes being present
    filtered_entries = {key: value for key, value in nested_dict.items() if has_all_attributes(value, attributes)}

    return filtered_entries

def filter_dict_by_key(data_dict: dict, dict_keys : str|list) -> dict:
    """
    Filters a dictionary to defined key(s)

    Args:
        data_dict (dict):   Data dictionary to filter
        dict_keys (str|list):    key(s) to search for in the dict values
    
    Returns:
        dict
    """

    if isinstance(dict_keys, str):
        # Single entry (convert to list for consistency)
        dict_keys = [dict_keys]

    # Filter based on all attributes being present
    filtered_entries = {key: value for key, value in data_dict.items() if key in dict_keys}

    return filtered_entries

def reformat_nested_dict(nested_dict: dict, attribute_key : str, attribute_value: str) -> dict :
    """
    Reformats a nested dictionary to a simple dict containing the two attributes as key:value pairs
    
    Args:
        nested_dict(dict):  Nested dictionary
        attribute_key:  Attribute to search for in nested_dict values and output as new key
        attribute_value:  Attribute to search for in nested_dict values and output as new value

    Returns:
        dict
    
    """
    #Filter to ensure that all attributes are present in each
    filtered_dict = filter_nested_dict_by_attribute(nested_dict, [attribute_key, attribute_value])
    #Reformat dict to the two atttributes in a new dict
    return {value[attribute_key] : value[attribute_value] for value in filtered_dict.values()}

def get_dict_entries(data_dict: dict, attribute_key: str, search_attribute : str, exclude_value: str = None, reverse : bool = False) -> dict :
    """
    Returns a dictionary containing only keys with a defined data type.

    Returns:
        field_ref (str):      Top level key that references a particular field in the dataschema_dict e.g. DATE
        attribute (str):      Attribute associated with the field_ref e.g. datatype
        reverse_selection (bool):   Bool to determine whether to include / exclude based on presence / absence of attribute
    """
    #Filter the entries to those containing the desired attribute
    dict_entries = {key : value for key, value in data_dict.items() if search_attribute in value}
    
    #Modify entries if needed
    if exclude_value is not None:
        if reverse:
            #Only include those containing the key
            return {value[attribute_key] : value[search_attribute] for value in dict_entries.values() 
                    if value[search_attribute] == exclude_value}
        #Exclude those containing the value
        return {value[attribute_key] : value[search_attribute] for value in dict_entries.values() 
                if value[search_attribute] != exclude_value}
    return {value[attribute_key] : value[search_attribute] for value in dict_entries.values()}
