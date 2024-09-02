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
    recursive = ("savanna", "metadata")
    selective = ("nomadic",)
    subfolders = recursive + selective
    divider = "*" * 80

    #Build list of subfolders as a string for user feedback
    subfolders_string = " and ".join(subfolders)

    print(divider)
    print(f"Identifying  all {subfolders_string} sequence data summaries and copying them to the output:")
    print(f"   Source: {seq_folder}")
    print(f"   Target: {output_folder}")

    #Pull out all entries that have the matching foldername
    matches = [folder for folder in identify_all_folders(seq_folder) if folder.name in subfolders]
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
        #Create the correct target path 
        relative_path = match.relative_to(seq_folder)
        target = output_folder.joinpath(relative_path)
        
        #Create the folder
        produce_dir(target)
        print(f"Copying {match.name} folder to {target}")
        
        #Copy files
        if match.name in selective:
            #Selectively copy only the top level folder and not subs to avoid fastq's etc
            extract_outputs(match, target, False)
        else:        
            #Copy entire tree structure over
            extract_outputs(match, target, True)

    print("Done")
    print(divider)