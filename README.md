# nmec-sequencing
## Overview
The idea here is to help streamline and standardise the storage of data generated on the NMEC server. In particular, we are trying to encourage:
- Standardised experiment names
- Standardised directory hierarchies
- Standardised metadata files

In addition, we hope to maintain an inventory of experiments and assays performed that we refer to with standardised codes. All of this will ensure data is useful and easily accessible over the life time of the project.
## Data Flow
All experimental data is produced using a standardised macro-enabled Excel template. VBA code extracts and outputs all of the relevent data from the experiment into two metadata csv files as follows:
```
EXPID_expt_metadata.csv   e.g. SLMM005_expt_metadata.csv
EXPID_rxn_metadata.csv    e.g. SLMM005_rxn_metadata.csv
```

EXPID_expt_metadata.csv: Contains a single row of text that contains all variables that are common to the entire experiment.
EXPID_rxn_metadata.csv: Contains as many rows as there are reactions performed with outputs unique to each reaction.

## Current status
As a start, I have produced a small script to automate some of the process of putting data on the NMEC Server:

```
$ python scripts/warehouse.py --help
Usage: warehouse.py [OPTIONS]

  Efficiently store sequencing data, automating the creation of directory
  structures, inventories, and validation of metadata

Options:
  -e, --expt_id TEXT       Experiment ID. For example MM-KP005.  [required]
  -m, --metadata_folder TEXT  Path to folder containing metadata CSV files. [required]
  --help                   Show this message and exit.

```

For example:

```
python scripts/warehouse.py \
-e SLMM005 \
-m path/to/metadatafolder/

```

The script will generate the experiment name, the directory hierarchy, and validate and move the metadata file to the appropriate location. In addition, it will prompt the user to update the inventories in `inventory` if features of the experiment are not yet documented.



