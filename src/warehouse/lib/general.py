import re
import configparser
from typing import Optional
from pathlib import Path
import logging

from warehouse.lib.exceptions import DataFormatError, PathError
from warehouse.lib.regex import Regex_patterns

#Get logging process
log = logging.getLogger("general")

def identify_exptid_from_path(path: Path) -> str:
    """
    Extract the experimental ID from a file or folder

    Args:
        path (Path): path to the folder

    Returns:
        expt_id (str): the extracted experiment id or None if not found
    """

    try:
        # First try with the path name
        match = re.search(Regex_patterns.NOMADS_EXPID, path.name)
        if match is None:
            # Second try with the full path
            match = re.search(Regex_patterns.NOMADS_EXPID, str(path))
        if match is None:
            raise DataFormatError(f"Unable to identify an ExpID in: {path}")

        return match.group(0)

    except StopIteration:
        msg = f"Unable to identify an ExpID in: {path.name}"
        log.debug(msg)
        raise DataFormatError(msg)


def identify_exptid_from_fn(path: Path) -> str | None:
    """
    Extract the experimental ID from a filename

    Args:
        path (Path): path to the file

    Returns:
        expt_id (str): the extracted experiment id or None if not found
    """

    try:
        match = re.search(Regex_patterns.NOMADS_EXPID, path.name)
        if match:
            expt_id = match.group(0)
            return expt_id

        return None

    except StopIteration:
        log.info(f"Unable to identify an ExpID in: {path.name}")
        return None


def identify_experiment_file(folder: Path, expt_id: str) -> Path | None:
    """
    Identify if there is an Excel file with a matching ExpID pattern in the list of filenames"

    Args:
    files_list (list): List of file paths.
    expt_id (str): Experiment ID to search for

    Returns:
        Path: The path to the matching file, or None if not found.
    """
    log.info("Searching for all NOMADS template files")
    matches = identify_files_by_search(
        folder, Regex_patterns.NOMADS_EXP_TEMPLATE, recursive=True
    )

    if not matches:
        return None

    log.info(f"Searching for files with {expt_id} in name")
    search_pattern = re.compile(f"{expt_id}")
    matches = [f for f in matches if search_pattern.search(f.name)]

    # Ensure there is at least one match
    if len(matches) == 0:
        raise ValueError("No matching files found.")
    elif len(matches) > 1:
        raise ValueError(f"Multiple matches found: {matches}")
    else:
        # Extract path from the  list object
        return matches[0]


def check_no_openfiles_identified(fn_list: list):
    """
    Identify if there are any files from a list that are currently open"

    Args:
    fn_list (list): List of file paths (pathlib).

    """
    # List all open files
    openfiles = [f for f in fn_list if Regex_patterns.OPENFILES.match(f.name)]
    # Ensure there are not any open files in the supplied list
    if openfiles:
        raise ValueError(
            f"{len(openfiles)} open files identified. Please close and run again:"
        )


def check_duplicate_names(entries):
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


def check_path_present(path: Path, isfile: bool):
    """
    Checks a path is present and whether it is a folder / file.

    Args:
    path (Path): path to the file or folder.
    isfile(bool): whether path should be a file or folder
    """
    if not path.exists():
        raise ValueError(f"{path} does not exist. Exiting...")

    if isfile and not path.is_file():
        raise PathError(f"Path should point to a file, but got a directory: {path}")
    elif not isfile and path.is_file():
        raise PathError(f"Path should point to a folder, but got a file: {path}")

def identify_all_folders(directory: Path, recursive: bool = False):
    """Recursively gets all folders within a directory.

    Args:
        directory (pathlib.Path): The root directory to search.
        recursive (bool): Whether to search recursively (default = False)

    Returns:
        A list of pathlib.Path objects representing all folders.
    """

    folders = []
    for path in directory.iterdir():
        if path.is_dir():
            folders.append(path)
            if recursive:
                folders.extend(identify_all_folders(path))
    return folders

def identify_all_files(folder: Path, recursive: bool = False) -> list[Path]:
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


def identify_files_by_search(
    folder_path: Path,
    pattern: re.Pattern,
    recursive: bool = False,
    verbose: bool = True,
) -> list[Path] | None:
    """
    Identify all files in a folder that match a search pattern"

    Args:
    folder_path (Path):     path to the search folder.
    pattern (re.pattern):   Compiled RE pattern to match filename against
    recursive (bool):       Select whether search should be recursive
    verbose (bool):         print outputs or now

    Returns:
        list[Path]: List of paths to the matching file(s), or None if not found.
    """

    try:
        matches = [
            f
            for f in identify_all_files(folder_path, recursive)
            if pattern.search(f.name)
        ]

        # Check that there are no open files
        check_no_openfiles_identified(matches)

        # Check there are no duplicate names
        check_duplicate_names(matches)

        # Ensure there is at least one match
        if len(matches) == 0:
            raise ValueError(f"No matching files found matching pattern: {pattern}")

        # Feedback to user what has been found
        if verbose:
            log.info(f"Found {len(matches)} matching file(s)")
        return matches

    except FileNotFoundError:
        log.info(f"Error: Folder '{folder_path.name}' not found.")
        return None

    except StopIteration:
        log.info(f"No matching file found matching pattern: {pattern}")
        return None

    except ValueError as error_msg:
        log.info(str(error_msg))
        raise


def produce_dir(*args, verbose: bool = True) -> Path:
    """
    Produce a new directory by concatenating `args`,
    if it does not already exist

    params
        *args: str1, str2, str3 ...
            Comma-separated strings which will
            be combined to produce the directory,
            e.g. str1/str2/str3

    returns
        dir: Path to directory name created from *args.

    """

    # Define directory path
    dir = Path(*args)
    
    # Create if doesn't exist
    if not dir.exists():
        dir.mkdir(parents=True, exist_ok=False)
        if verbose:
            log.info(f"   {dir.absolute()} created")

    return dir


def create_dict_from_ini(ini_files: Path | list[Path]) -> dict:
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
    field_dict: dict[str, dict] = {}

    for ini_file in ini_files:
        config = configparser.ConfigParser()
        config.read(ini_file)

        for section, items in config.items():
            for key, value in items.items():
                # Enter the key and value into dict
                field_dict.setdefault(key.upper(), {})[section] = value
    return field_dict


def get_nested_key_value(data_dict: dict, key: str, nested_key: str) -> str | dict:
    """
    Retrieves the label for a given key from the dictionary.

    Args:
        key (str): The key of the field to get values from (uppercase)
        nested_key: The nested key of field to get values from

    Returns:
        str|dict: The value for the nested_key, or None if not found.
    """

    return data_dict.get(key, {}).get(nested_key)


def filter_nested_dict_by_attribute(nested_dict: dict, attributes: str | list) -> dict:
    """
    Filters a nested dictionary to those containing a specific attribute

    Args:
        nested_dict (dict):   Nested dictionary to filter
        attribute (str|list):    Attribute(s) to search for in the dict values

    Returns:

    """

    def has_all_attributes(value: dict, attributes: list) -> bool:
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
    filtered_entries = {
        key: value
        for key, value in nested_dict.items()
        if has_all_attributes(value, attributes)
    }

    return filtered_entries


def filter_dict_by_key_or_value(data_dict: dict, dict_term: str | list, search_key: bool = True) -> dict:
        """
        Filters a dictionary to defined key(s)

        Args:
            data_dict (dict):       Data dictionary to filter
            dict_keys (str|list):   key(s) to search for in the dict values

        Returns:
            dict
        """

        if isinstance(dict_term, str):
            # Convert to set for consistency
            dict_term = [ dict_term ]
            
        # Filter for attribute in key or value
        if search_key:
            filtered_entries = {
                key: value for key, value in data_dict.items() if any(item in key for item in dict_term)
            }
        else:
            filtered_entries = {
                key: value for key, value in data_dict.items() if any(item in value for item in dict_term) 
            }

        return filtered_entries


def reformat_nested_dict(
    nested_dict: dict, attribute_key: str, attribute_value: str
) -> dict:
    """
    Reformats a nested dictionary to a simple dict containing the two attributes as key:value pairs

    Args:
        nested_dict(dict):  Nested dictionary
        attribute_key:  Attribute to search for in nested_dict values and output as new key
        attribute_value:  Attribute to search for in nested_dict values and output as new value

    Returns:
        dict

    """
    # Filter to ensure that all attributes are present in each
    filtered_dict = filter_nested_dict_by_attribute(
        nested_dict, [attribute_key, attribute_value]
    )
    # Reformat dict to the two atttributes in a new dict
    return {
        value[attribute_key]: value[attribute_value] for value in filtered_dict.values()
    }


def filter_nested_dict(
    nested_dict: dict,
    new_key_field: str,
    new_value_field: str,
    exclude_value: Optional[str] = None,
    reverse: bool = False,
) -> dict:
    """
    Returns a dictionary containing entries with a defined nested key.

    Args:
        nested_dict (dict):     Nested Dictionary
        new_key_field(str):     Nested field to use as key
        new_value_field (str):  Nested field to use as value
        exclude_value:          Nested field to filter on
        reverse (bool):         Whether to filter in (True) or out (False)

    Returns:
        dict:           All entries that fulfill the input requirements
    """
    # Filter to ensure that the entries contain both the new key and new value entries
    dict_entries=filter_dict_by_key_or_value(nested_dict, new_value_field, search_key=False)
    dict_entries=filter_dict_by_key_or_value(dict_entries, new_key_field, search_key=False)    

    #If no exclude value then create a dict with the attribute_key
    if exclude_value is None:
        return {value[new_key_field]: value[new_value_field] for value in dict_entries.values()}
    
    # Only include those containing the key
    if reverse:
        return {
            value[new_key_field]: value[new_value_field]
            for value in dict_entries.values()
            if value[new_value_field] == exclude_value
        }
    
    # Exclude all entries containing the exclude_value
    return {    
        value[new_key_field]: value[new_value_field]
        for value in dict_entries.values()
        if value[new_value_field] != exclude_value
    }