import os
from pathlib import Path
import configparser
from lib.general import produce_dir

class ExperimentDirectories:
    """

    """

    def __init__(self, expt_name: str, root_folder: Path, dir_ini: Path ):
        """
        Initialise all the required directories

        """
        
        if root_folder:
            ROOT_DIR = root_folder.absolute()
            self.experiments_dir = produce_dir(ROOT_DIR)
        else:
            ROOT_DIR = Path(__file__).absolute().parent.parent.parent
            self.experiments_dir = produce_dir(ROOT_DIR, "experiments")
        # Experiment directory
        self.expt_name = expt_name
        self.expt_dir = produce_dir(self.experiments_dir, expt_name)
        
        if dir_ini is None:
            print(" No .ini file supplied")
            script_dir = Path.cwd()
            dir_ini = script_dir / "scripts/nomadic/dir_structure.ini"
            print(" Using default .ini file")

        if not os.path.exists(dir_ini) :
            print(" Default ini file not found, using standard structure")
            #Create hard coded default dirs
            self.metadata_dir = produce_dir(self.expt_dir, "metadata")
            self.minknow_dir = produce_dir(self.expt_dir, "minknow")
            self.nomadic_dir = produce_dir(self.expt_dir, "nomadic")
        
        print(" Importing .ini file")
        config = configparser.ConfigParser()
        config.read(dir_ini)

        #Process entries in the default section
        for default_key, default_value in config.items("default"):
            #Produce the relevent directories
            produce_dir(self.expt_dir, default_value)
            #set an attribute for further ref
            att_name = default_key + "_dir"
            att_value = self.expt_dir + "/" + default_value
            setattr(self, att_name, att_value)
            
            #Produce any defined sub-directories
            if config.has_section(default_key):
                for sub_key, sub_value in config.items(default_key):
                    produce_dir(self.expt_dir, default_value, sub_value)
