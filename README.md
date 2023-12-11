# warehouse
## Overview
The idea for this repo is to  help streamline and standardise the storage of data generated from NOMADS assays. In particular, we are trying to encourage:
- Standardised experiment names
- Standardised directory hierarchies
- Standardised metadata files

In addition, we hope to maintain an inventory of experiments and assays performed that we refer to with standardised codes. All of this will ensure data is useful and easily accessible over the life time of the project.

## Data Flow
All experimental data is produced using a standardised Excel template. Originally this was exported using VBA code, but can now be extracted en masse with warehouse. and outputs Either way, all of the relevent data from the experiment is exported into two metadata csv files as follows:
```
EXPID_expt_metadata.csv   e.g. SLMM005_expt_metadata.csv
EXPID_rxn_metadata.csv    e.g. SLMM005_rxn_metadata.csv
```

EXPID_expt_metadata.csv: Contains a single row of text that contains all variables that are common to the entire experiment.
EXPID_rxn_metadata.csv: Contains as many rows as there are reactions performed with outputs unique to each reaction.

## Usage

```
$ python scripts/warehouse.py --help
Usage: warehouse.py [OPTIONS] COMMAND [ARGS]...

  NOMADS Sequencing Data - experimental outputs

Options:
  --help  Show this message and exit.

Commands:
  extract   Extract metadata tables from Excel experimental worksheets
  metadata  Combine and check all metadata files and export aggregate to csv
            in metadata folder
  nomadic   Create nomadic directory structure and copy metadata from a
            sequencing experiment

```

For example:

```
python scripts/warehouse.py nomadic -e SLMM005 -m path/to/metadatafolder/

```

The script will generate the experiment name, the directory hierarchy, validate and move the metadata file to the appropriate location.
