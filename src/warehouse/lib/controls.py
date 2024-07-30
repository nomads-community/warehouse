import os
from pathlib import Path
import configparser
from warehouse.lib.decorators import singleton

@singleton
class load_controls:
    """
    Load information on control strains used in the project so that they can be isolated from samples.
    """

    def __init__(self, controls_ini: Path = None) -> dict:
        """
        Pull in controls data from .ini file

        """
        
        if controls_ini is None:
            print(" No .ini file supplied")
            script_dir = Path.cwd()
            controls_ini = script_dir / "scripts/lib/controls.ini"
            print(" Using default .ini file")
        
        if not os.path.exists(controls_ini) :
            raise ValueError(f"Unable to find {controls_ini}")
        
        config = configparser.ConfigParser()
        config.read(controls_ini)

        # Create an empty dictionary to store data
        controls_dict = {}

        # Create an empty dictionary to store data
        controls_dict = {}

        # Iterate through sections (excluding default section)
        for section in config.sections():
            # Create a sub-dictionary for each section
            section_dict = {}
            for key, value in config.items(section):
                section_dict[key] = value
            # Add the section data to the main dictionary
            controls_dict[section] = section_dict

        self.controls_dict = controls_dict