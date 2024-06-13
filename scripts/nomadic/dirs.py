import os
from pathlib import Path
import configparser
# import dataclass
from dataclasses import dataclass


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
        print(f"   {dir_name}")

    return dir_name

@dataclass
class DataStructure:
    #Create config object and pull in ini
    config = configparser.ConfigParser()
    config.read('./default_dir_structure.ini')  # Replace 'config.ini' with your actual file path
    print(config)



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
            print(" No ini file given, searching for default")
            script_dir = Path.cwd()
            dir_ini = script_dir / "scripts/nomadic/dir_structure.ini"

        if not os.path.exists(dir_ini) :
            print(" Default ini missing using standard structure")
            # Metadata directory
            self.metadata_dir = produce_dir(self.expt_dir, "metadata")
            
            # MinKNOW directory
            self.minknow_dir = produce_dir(self.expt_dir, "minknow")

            # Guppy directory
            self.guppy_dir = produce_dir(self.expt_dir, "guppy")

            # NOMADIC directories
            self.nomadic_dir = produce_dir(self.expt_dir, "nomadic")
            _ = produce_dir(self.nomadic_dir, "mpi")
            _ = produce_dir(self.nomadic_dir, "nmec")
        else:
            print(" Found default .ini file")
        

        print(" Importing .ini file")
        config = configparser.ConfigParser()
        config.read(dir_ini)

        for default_key, default_value in config.items("default"):
            #Produce the relevent directories
            produce_dir(self.expt_dir, default_value)
            #set an attribute for further ref
            att_name = default_key + "_dir"
            att_value = self.expt_dir + "/" + default_value
            setattr(self, att_name, att_value)
            
            #Produce the relevent sub-directories
            if config.has_section(default_key):
                for sub_key, sub_value in config.items(default_key):
                    produce_dir(self.expt_dir, default_value, sub_value)
            

        

        