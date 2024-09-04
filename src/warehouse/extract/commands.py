from pathlib import Path
import click
from warehouse.lib.general import produce_dir, identify_all_folders
from .extract import extract_outputs

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
    help="Path to folder where the summary sequencing outputs in a mirror hierarchy should be generated",
)

def extract(seq_folder: Path, output_folder: Path):
    #Dict lisitng name of folder as key and then "all" for all subs or list of subfolders to copy
    targets = { "savanna" : {"recursive" : True, "subfolders" :  []}, "nomadic" : {"recursive" : False, "subfolders" : ["metadata"] }}
    divider = "*" * 80

    #Build list of subfolders as a string for user feedback
    target_list = list(targets.keys())
    target_string = ", ".join(target_list[:-1]) + " and " + target_list[-1]

    print(divider)
    print(f"Identifying sequence data summaries from {target_string} and copying them to the output folder:")
    print(f"   Source: {seq_folder}")
    print(f"   Target: {output_folder}")

    #Pull out all entries that have the matching foldername
    matches = [folder for folder in identify_all_folders(seq_folder) if folder.name in targets]
    print(f"   Found {len(matches)} matches")
    print(divider)

    if len(matches) == 0 :
        print("No matches found.")
        print(divider)
        exit()

    print("Processing all files and folders")
    produce_dir(output_folder)

    #Process each match
    for match in matches:
        #Identify any subfolders to also copy
        recursive = targets.get(match.name)["recursive"]
        
        #Create a list with the original match
        copyfolders=[match]
        if not recursive:
            #Add in all the subfolders
            for subfolder in targets.get(match.name)["subfolders"] :
                copyfolders.append(match / subfolder)

        for folder in copyfolders:      
            #Create the correct target path 
            relative_path = folder.relative_to(seq_folder)
            target = output_folder.joinpath(relative_path)

            #Create the folder
            produce_dir(target)
            print(f"Copying {folder.name} folder to {target}")
            
            if recursive:
                #Copy entire tree structure over
                extract_outputs(folder, target, True)
            else:
                #Selectively copy the top level folder
                extract_outputs(folder, target, False)

    print("Done")
    print(divider)