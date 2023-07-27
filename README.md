# nmec-sequencing
## Overview
The idea here is to help streamline and standardise the storage of data generated on the NMEC server. In particular, we are trying to encourage:
- Standardised experiment names
- Standardised directory hierarchies
- Standardised metadata files

In addition, we hope to maintain an inventory of sample sets and assays that we refer to with standardised codes. All of this will ensure data is useful and easily accessible over the life time of the project.

## Current status
As a start, I have produced a small script to automate some of the process of putting data on the NMEC Server:

```
$ python scripts/warehouse.py --help
Usage: warehouse.py [OPTIONS]

  Efficiently store sequencing data, automating the creation of directory
  structures, inventories, and validation of metadata

Options:
  -d, --expt_date TEXT     Date experiment was conducted.  [required]
  -e, --expt_id TEXT       Experiment ID. For example MM-KP005.  [required]
  -s, --sample_set TEXT    Sample set ID. For example TES2022.  [required]
  -a, --assay TEXT         Assay ID. For example NOMADS8.  [required]
  -m, --metadata_csv TEXT  Path to metadata CSV.  [required]
  --help                   Show this message and exit.

```

For example:

```
python scripts/warehouse.py \
-d 2023-07-26 \
-e MM-KP005 \
-s TES2022 \
-a NOMADS 8 \
-m path/to/metadata.csv

```

The script will generate the experiment name, the directory hierarchy, and validate and move the metadata file to the appropriate location. In addition, it will prompt the user to update the inventories in `inventory` if features of the experiment are not yet documented.



