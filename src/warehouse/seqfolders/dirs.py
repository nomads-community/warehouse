from pathlib import Path
import configparser
from warehouse.lib.general import produce_dir


class ExperimentDirectories:
    """
    Creation of NOMADS folder structure for data storage
    """

    def __init__(
        self, expt_name: str, output_folder: Path = None, dir_ini: Path = None
    ):
        """
        Initialise all the required directories

        """
        # Define where the script is running from so you can reference internal files etc
        warehouse_dir = Path(__file__).parent.parent.parent.parent.resolve()
        script_dir = Path(__file__).parent.resolve()

        if output_folder:
            self.experiments_dir = produce_dir(str(output_folder))
        else:
            self.experiments_dir = produce_dir(warehouse_dir, "experiments")
        # Experiment directory
        self.expt_name = expt_name
        self.expt_dir = produce_dir(self.experiments_dir, expt_name)

        if not dir_ini:
            print(" No .ini file supplied, using default")
            dir_ini = script_dir / "dir_structure.ini"

        # Read in the values from the ini file
        config = configparser.ConfigParser()
        config.read(dir_ini)

        # Process entries in the default secti   on
        for default_key, default_value in config.items("default"):
            # Produce the relevent directories
            produce_dir(self.expt_dir, default_value)
            # set an attribute for further ref
            att_name = default_key + "_dir"
            att_value = self.expt_dir + "/" + default_value
            setattr(self, att_name, att_value)

            # Produce any defined sub-directories
            if config.has_section(default_key):
                for sub_key, sub_value in config.items(default_key):
                    produce_dir(self.expt_dir, default_value, sub_value)

        print(" All folders created / available in:")
        print(f"   {self.expt_dir}")
