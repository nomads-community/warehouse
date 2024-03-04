import os
from pathlib import Path


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

    return dir_name


class ExperimentDirectories:
    """

    """

    def __init__(self, expt_name: str, root_folder: Path):
        """
        Initialise all the required directories

        """
        
        if root_folder:
            ROOT_DIR = root_folder.absolute()
        else:
            ROOT_DIR = Path(__file__).absolute().parent.parent.parent
        # Experiment directory
        self.experiments_dir = ROOT_DIR
        self.expt_name = expt_name
        self.expt_dir = produce_dir(self.experiments_dir, expt_name)

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

        