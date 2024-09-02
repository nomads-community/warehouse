from pathlib import Path
import shutil

def extract_outputs(source_dir: Path, target_dir: Path, recursive: bool = False):
    """Copies contents of a folder to a new location.

    Args:
        source_dir(Path): The path to the source folder
        target_dir(Path): The path to the target folder
        recursive(bool): Copy top-level files or entire directory
    """
    if recursive:
        shutil.copytree(source_dir, target_dir  , dirs_exist_ok=True)
    else:
        for path in source_dir.iterdir():
            if path.is_file():
                shutil.copy2(path, target_dir)