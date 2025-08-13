import logging
from pathlib import Path

import yaml

from warehouse.lib.decorators import singleton
from warehouse.lib.exceptions import GenError, PathError
from warehouse.lib.logging import minor_header

# Get logging process
log = logging.getLogger(Path(__file__).stem)


script_dir = Path(__file__).parent.resolve()


@singleton
def load_warehouse_configuration_dict() -> dict:
    config_file = script_dir / "warehouse_config.yml"
    if not config_file.exists():
        raise PathError("No configuration file found. Please run 'warehouse configure'")
    minor_header(log, "Loading warehouse configuration:")
    with open(config_file, "r") as f:
        config_dict = yaml.safe_load(f)
    return config_dict


def get_configuration_value(config_key: str) -> Path | str:
    config_dict = load_warehouse_configuration_dict()
    value = config_dict.get(config_key, "")
    # Check if empty
    if (not value) and (value is not False):
        raise GenError(f"Unable to identify {config_key}")

    # Check if a path
    if isinstance(value, str) and ("/" in value or "\\" in value):
        return Path(value)
    return value


def select_int_from_list(options: list):
    print("Please select an option:")
    for i, option in enumerate(options):
        print(f"{i + 1}. {option}")

    while True:
        try:
            choice = int(input("Enter the number of your choice: "))
            if 1 <= choice <= len(options):
                # return the zero indexed selection
                return choice - 1
            else:
                print("Invalid choice. Please enter a number within the range.")
        except ValueError:
            log.info("Invalid input. Please enter a number.")
