from pathlib import Path
import click
from warehouse.lib.general import identify_all_folders
from .extract import process_targets

@click.command(short_help="Copy sequence data summary outputs from nomadic and / or savanna into standardised hierarchy for synchronisation.")
@click.option(
    "-s",
    "--seq_folder",
    type=Path,
    required=True,
    help="Path to folder containing sequencing outputs with seqfolders structure",
)
@click.option(
    "-o",
    "--output_folder",
    type=Path,
    required=False,
    help="Path to folder where the sequencing outputs should be copied to",
)

def extract(seq_folder: Path, output_folder: Path):
    """
    Extract sequence data summaries for sharing 
    """

    #Dict lisitng name of folder as key and then "all" for all subs or list of subfolders to copy
    targets = { 
        "savanna" : {
            "name" : "savanna",
            "recursive" : False, 
            "subfolders" : {
                "summary" :{ 
                    "name" : "summary", "recursive" : True}
                }
            },
        "nomadic" : {
            "name" : "nomadic" ,
            "recursive" : False
            },
        "metadata" : {
            "name" : "metadata" ,
            "recursive" : False
            }
        }

    divider = "*" * 80

    #Build list of subfolders as a string for user feedback
    target_list = list(targets.keys())
    target_string = ", ".join(target_list[:-1]) + " and " + target_list[-1]
    
    print(divider)
    print(f"Identifying sequence data summaries from {target_string} and copying them to the output folder:")
    print(f"   Source: {seq_folder}")
    print(f"   Target: {output_folder}")

    #Identify all experimental folders
    all_folders = [folder for folder in identify_all_folders(seq_folder, True) ]
    exp_folders = [folder for folder in identify_all_folders(seq_folder) ]
    
    for exp_folder in all_folders:
        if exp_folder in exp_folders:
            print("")
            print(divider)
            print(f"Copying {exp_folder.name}")
            print("")
        #Get the relative path
        relative_path = exp_folder.relative_to(seq_folder)
        target_folder = output_folder / relative_path
        process_targets(targets, exp_folder, target_folder)
    
    print(divider)