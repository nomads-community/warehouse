import configparser
import logging
from pathlib import Path
from typing import Optional

import yaml

from warehouse.lib.general import check_path_present

# Get logging process
log = logging.getLogger("general")

# Define where the script is running from so you can reference internal files etc
script_dir = Path(__file__).parent.resolve()


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


def create_dict_from_yaml(yaml_files: Path | list[Path]) -> dict:
    """
    Define fields from a .yml file(s) into a dictionary

    Args:
        yml_files list[Path]: Path(s) to yml file

    Returns:
        dict:   dictionary containing all details from yml file(s)
    """
    if isinstance(yaml_files, Path):
        # Single entry (convert to list for consistency)
        yaml_files = [yaml_files]

    # Create an empty dictionary to store data
    yml_dict: dict[str, dict] = {}
    # Loop through each file and load the YAML content
    log.debug(f"Loading YAML files: {yaml_files}")
    for yml in yaml_files:
        with open(yml, "r") as f:
            tmp_dict = yaml.safe_load(f)
            yml_dict.update(tmp_dict)
    return yml_dict


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


def filter_dict_by_key_or_value(
    dict_to_filter: dict, search_term: str | list, search_key: bool = True
) -> dict:
    """
    Filters a dictionary to defined key(s)

    Args:
        data_dict (dict):       Data dictionary to filter
        dict_term (str|list):   Term to search for in the dict
        search_key (bool):      Bool test to search the key field

    Returns:
        dict
    """

    if isinstance(search_term, str):
        # Convert to a list for consistency
        search_term = [search_term]

    # Filter for attribute in key or value
    if search_key:
        filtered_entries = {
            key: value
            for key, value in dict_to_filter.items()
            if any(item in key for item in search_term)
        }
    else:
        filtered_entries = {
            key: value
            for key, value in dict_to_filter.items()
            if any(item in value for item in search_term)
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
    dict_entries = filter_dict_by_key_or_value(
        nested_dict, new_value_field, search_key=False
    )
    dict_entries = filter_dict_by_key_or_value(
        dict_entries, new_key_field, search_key=False
    )

    # If no exclude value then create a dict with the attribute_key
    if exclude_value is None:
        return {
            value[new_key_field]: value[new_value_field]
            for value in dict_entries.values()
        }

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


def merge_dataschema_dicts_with_suffixes(dict_list: list, suffix_list: list) -> dict:
    """
    Merges a list of dataschema dictionaries together. Duplicate keys are suffixed according
    to the dict they come from.

    Args:
        dict_list(list) : List of dictionaries to merge
        suffix_list(list)   List of suffixes to append to duplicates

    Returns:
        dict:   Merged dictionary
    """
    if len(dict_list) != len(suffix_list):
        raise ValueError("The number of dictionaries and suffixes must be the same.")

    merged_data = {}
    key_occurrence_info = {}

    for i, current_dict in enumerate(dict_list):
        # Set the current suffix
        current_suffix = suffix_list[i]

        for key, value in current_dict.items():
            # If the key has been seen before
            if key in key_occurrence_info:
                # Add suffix to the key and to the nested field name
                suffixed_value = {
                    "field": f"{value['field']}_{current_suffix}",
                    "label": f"{value['label']}",
                }
                merged_data[f"{key}_{current_suffix.upper()}"] = suffixed_value
                key_occurrence_info[key]["occurrences"].append(i)
            else:
                # First time seeing this key so add to dict
                merged_data[key] = value
                # Add info on having seen this key before
                key_occurrence_info[key] = {"occurrences": [i]}

    # Ensure all duplicate keys from the first processed dictionary are properly suffixed
    for key, info in key_occurrence_info.items():
        # Identify keys that appeared in the first dict and in more than one dict
        if len(info["occurrences"]) > 1 and 0 in info["occurrences"]:
            # Get the entry in the first dict
            orig_value = dict_list[0][key]
            # Build the suffixed version
            suffixed_value = {
                "field": f"{orig_value['field']}_{suffix_list[0]}",
                "label": f"{orig_value['label']}",
            }
            # Add in new entry
            merged_data[f"{key}_{suffix_list[0].upper()}"] = suffixed_value

    return merged_data


def add_suffix_to_duplicate_dict_entries(
    current_dict: dict,
    dict_to_test: dict,
    suffix: str,
) -> dict:
    """
    Tests each key in current_dict against all keys in dict_to_test. If a match is found
    then a suffixed entry is added to the current_dict

    Args:
        current_dict (dict): The dictionary to which new entries will be merged
        dict_to_test (dict): The dictionary whose entries are checked for conflict with current_dict
        suffix (str): The suffix to use for the current dict being merged

    Returns:
        dict: Returns an updated `current_dict` with suffixed entries.
    """
    new_dict = {}
    # Go through each key-value pair in the dict_to_add
    for key, value in current_dict.items():
        if key in dict_to_test:
            # First add the original entry back in
            new_dict[key] = value
            # Determine if the key is upper case and therefore whether the suffix should follow suit
            if key.isupper():
                # Generate a new unique upper prefixed key
                new_key = f"{key}_{suffix.upper()}"
            else:
                new_key = f"{key}_{suffix}"

            # Ensure the newly generated keys are not in the existing_dict
            if new_key in current_dict:
                log.debug(f"{new_key} already in curent dict")
            elif new_key in dict_to_test:
                log.debug(f"{new_key} already in existing dict")

            # Modify the values to also include the prefixes if it is a dict
            if type(value) is dict:
                newvalue = value.copy()
                newvalue["field"] = f"{value.get('field')}_{suffix}"
            elif type(value) is str:
                newvalue = f"{value}_{suffix}"
            # Add entries to dict
            new_dict[new_key] = newvalue

            log.debug(f"Duplicate key found: {key}")
            log.debug(f"   Added '{new_key} : {newvalue}'")

        else:
            # Not a duplicate so add
            new_dict[key] = value
            log.debug(f"Added new key: '{key}'.")
    return new_dict


def create_datasources_dict(metadata_fn_path: Path = None) -> dict:
    """
    Creates a dictionary mapping data source names to lists of their
    dataschema yaml filepaths along with user defined sample metadata file.
    Args:
        metadata_fn_path (Path):
            User defined sample metadata file (e.g., an `.xlsx` file). Its parent directory and stem will
            be used to derive the path to the corresponding sample metadata YAML file.

    Returns:
        dict: Keys are the category of the data, with nested source name and absolute path"""
    # Get the default data sources
    dataschemas_dir = script_dir.parent / "metadata" / "dataschemas"
    datasources_yml = dataschemas_dir / "datasources.yml"
    datasources = create_dict_from_yaml(datasources_yml)

    # Transform the dict to have paths to each target yml file
    for category in datasources.keys():
        # Get the sourcenames and ensure in a list
        sources = datasources[category].get("sources")
        # Translate sourcenames into paths
        paths = [dataschemas_dir / category / f"{s}.yml" for s in sources]
        datasources[category]["paths"] = paths

    if metadata_fn_path:
        metadata_yml = metadata_fn_path.parent / f"{metadata_fn_path.stem}.yml"
        check_path_present(metadata_yml, isfile=True, raise_error=True)
        # Add entry to dict
        datasources["metadata"] = {"category_label": "Sample Metadata"}
        datasources["metadata"]["sources"] = [metadata_yml.name]
        datasources["metadata"]["source_labels"] = [metadata_yml.stem]
        datasources["metadata"]["paths"] = [metadata_yml]

    return datasources
