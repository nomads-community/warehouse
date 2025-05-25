import configparser
import logging
from pathlib import Path
from typing import Optional

# Get logging process
log = logging.getLogger("general")


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


def filter_dict_by_key_or_value(
    data_dict: dict, dict_term: str | list, search_key: bool = True
) -> dict:
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
        dict_term = [dict_term]

    # Filter for attribute in key or value
    if search_key:
        filtered_entries = {
            key: value
            for key, value in data_dict.items()
            if any(item in key for item in dict_term)
        }
    else:
        filtered_entries = {
            key: value
            for key, value in data_dict.items()
            if any(item in value for item in dict_term)
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
