# warehouse
## Overview
The idea for this repository is to help streamline and standardise the storage of data generated from NOMADS assays. In particular, we are trying to encourage:
- Standardised experiment names
- Standardised directory hierarchies
- Standardised metadata files

## Data Flow
All experimental data is produced using a standardised Excel template. In every template there are user-friendly tabs for entry of data. Key user-entered data elements are then summarised in two Excel tables as follows:

- expt_metadata - experiment-wide data e.g. date of experiment
- rxn_metadata - reaction level data e.g. post-PCR DNA concentration

Originally VBA code in the spreadsheet was used to export individual data tables to csv files. `warehouse` can now directly import, munge and export data as required.

## Install

#### Requirements

To install `warehouse`, you will need:
- Version control software [git](https://github.com/git-guides/install-git)
- Package manager [mamba](https://github.com/conda-forge/miniforge) 

#### Steps

**1.  Clone the repository from github:**
```
git clone https://github.com/nomads-community/warehouse
cd warehouse
```

**2.  Install the dependencies with mamba:**
```
mamba env create -f environment.yml
```

**3. Open the `warehouse` environment:**
```
mamba activate warehouse
```

## Usage

```
$ python scripts/warehouse.py --help
Usage: warehouse.py [OPTIONS] COMMAND [ARGS]...

  NOMADS Sequencing Data - experimental outputs

Options:
  --help  Show this message and exit.

Commands:
  metadata  Extract, validate and optionally export all metadata
  nomadic   Create nomadic directory structure and copy metadata from a
            sequencing experiment

```

## Examples
- Extract, validate and output all data into a series of csv files for each experiment:
```
python scripts/warehouse.py metadata -m example_data/ -o ./`
```

- Create standardised directory hierarchy, validate metadata and create output file for downstream tools: 
```
python scripts/warehouse.py nomadic -m example_data/ -e SLJS034
```