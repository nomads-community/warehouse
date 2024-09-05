from pathlib import Path
import subprocess

def extract_outputs(source_dir: Path, target_dir: Path, recursive: bool = False):
    """Copies contents of a folder to a new location.

    Args:
        source_dir(Path): The path to the source folder
        target_dir(Path): The path to the target folder
        recursive(bool): Copy top-level files or entire directory
    """

    if recursive:
        rsync_command = ["rsync", "-zvrc", source_dir, target_dir]
        # shutil.copytree(source_dir, target_dir  , dirs_exist_ok=True)
    else:
        rsync_command = ["rsync", "-vzrc", "--exclude", "*/", f"{source_dir.as_posix()}/", target_dir]   
        # for path in source_dir.iterdir():
        #     if path.is_file():
        #         shutil.copy2(path, target_dir)
    
    subprocess.run(rsync_command)
    # Working rsync
    #rsync -zvc /folderpath/* folderoutput
    #This won't expand the * above 
    #rsync -vzrc --exclude "*/" folderinput/ folderoutput
    # This won't add the trailing slash on folderinput

