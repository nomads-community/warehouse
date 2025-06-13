import logging
import re
from pathlib import Path

from warehouse.lib.exceptions import DataFormatError
from warehouse.lib.regex import Regex_patterns

# Get logging process
log = logging.getLogger("general")


def identify_exptid_from_path(path: Path, raise_error: bool = True) -> str:
    """
    Extract the experimental ID from a file or folder

    Args:
        path (Path): path to the folder

    Returns:
        expt_id (str): the extracted experiment id or None if not found
    """

    try:
        # First try with the
        match = re.search(Regex_patterns.NOMADS_EXPID, path.name)
        if match is None:
            # Second try with the full path
            match = re.search(Regex_patterns.NOMADS_EXPID, str(path))
        if match is None:
            if raise_error:
                raise DataFormatError(f"Unable to identify an ExpID in: {path}")
            return None

        return match.group(0)

    except StopIteration:
        msg = f"Unable to identify an ExpID in: {path.name}"
        log.debug(msg)
        raise DataFormatError(msg)


def extract_exptype_from_expid(expid: str, raise_error: bool = True) -> str:
    """
    Identify the experimental type from the expid

    Args:
        expid (str): Experiment ID

    Returns:
        expt_type (str): the extracted experiment type or None if not found
    """

    exp_type = (
        expid[0:2].replace("PC", "PCR").replace("SL", "seqlib").replace("SW", "sWGA")
    )

    if len(exp_type) == 2:
        raise DataFormatError(f"Unable to identify an Experiment type in: {expid}")

    return exp_type


def identify_experiment_files(folder: Path, expt_ids: list) -> list:
    """
    Identify if there is an Excel file with a matching ExpID pattern in the list of filenames"

    Args:
        files_list (list): List of file paths.
        expt_id (str): Experiment ID to search for

    Returns:
        list(Path): List of path(s) to the matching file(s)
    """
    if isinstance(expt_ids, str):
        expt_ids = [expt_ids]

    log.info("Searching for all NOMADS template files")
    template_files = identify_files_by_search(
        folder, Regex_patterns.NOMADS_EXP_TEMPLATE, recursive=True
    )
    if not template_files:
        raise ValueError("No NOMADS template files found.")

    filepaths = []
    for expt_id in expt_ids:
        log.info(f"   Searching for {expt_id} in filename")
        search_pattern = re.compile(f"{expt_id}")

        matches = [f for f in template_files if search_pattern.search(f.name)]

        # Ensure there is at least one match
        if len(matches) == 0:
            raise ValueError(f"No matching files found for {expt_id}.")
        elif len(matches) > 1:
            raise ValueError(f"Multiple matches found: {matches}")
        else:
            # Extract path from the  list object
            filepaths.append(matches[0])
    return filepaths


def check_no_openfiles(fn_list: list):
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


def check_path_present(
    path: Path, isfile: bool = False, raise_error: bool = False
) -> bool:
    """
    Checks a path is present and whether it is a folder / file.

    Args:
        path (Path): path to the file or folder.
        isfile(bool): whether path should be a file or folder
        raise_error (bool): raise an error if the path is not present

    Returns:
        bool result
    """
    if not path.exists():
        if raise_error:
            raise FileNotFoundError(f"Path '{path}' does not exist. Exiting...")
        return False

    if isfile and not path.is_file():
        if raise_error:
            raise IsADirectoryError(
                f"Path '{path}' should point to a file, but its a directory"
            )
        return False
    elif not isfile and path.is_file():
        if raise_error:
            raise NotADirectoryError(
                f"Path should point to a folder, but got a file: {path}"
            )
        return False

    return True


def identify_single_folder(
    folder_path: Path, pattern, recursive: bool = False, verbose: bool = False
) -> Path | None:
    """
    Identify a single target folder using a pattern

    Args:
      path: The path to the directory as a Path object.
      pattern: The pattern to search for.
    """
    log.debug(
        f"folder_path={folder_path}, pattern={pattern}, recursive={recursive}, verbose={verbose}"
    )
    folders = identify_files_by_search(
        folder_path=folder_path,
        pattern=pattern,
        recursive=recursive,
        verbose=verbose,
    )

    if len(folders) != 1:
        return None

    return folders[0]


def identify_folders_by_pattern(folder: Path, pattern: str) -> list[Path]:
    """
    Searches for folders within a given root directory whose names match the provided regular expression pattern.

    Args:
      root_dir: The root directory to search within.
      pattern: The regular expression pattern to match against folder names.

    Returns:
      A list of Path objects representing the folders that match the pattern.
    """

    path = Path(folder)
    matching_folders = []

    if not path.exists():
        return matching_folders

    for folder in path.iterdir():
        if folder.is_dir() and re.search(pattern, folder.name):
            matching_folders.append(folder)

    return matching_folders


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
    verbose (bool):         print outputs or not

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
        check_no_openfiles(matches)

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


def is_directory_empty(directory_path: Path, raise_error: bool = True) -> bool:
    """Checks if a directory is empty.

    Args:
      directory_path: The path to the directory to check.

    Returns:
      True if the directory is empty, False otherwise.
    """
    # Ensure it is a pathlib object
    path = Path(directory_path)

    # Check if it is a dir, error if not
    if not path.is_dir():
        if raise_error:
            raise ValueError(f"{directory_path} is not a directory.")
        return False

    # Check if path is empty
    if not any(path.iterdir()):
        return True
    # Otherwise it has contents
    return False


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


def pad_list(dictionary: dict, key: str, padlength: int) -> list:
    details = dictionary.get(key)
    details = details + [""] * (padlength - len(details))
    return details
