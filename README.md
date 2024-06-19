# warehouse
## Overview
The idea for this repository is to help streamline and standardise the storage of data generated from NOMADS assays. In particular, we are trying to encourage:
- Standardised experiment names
- Standardised directory hierarchies
- Standardised metadata files

## Data Flow
### Experimental 
All experimental data is produced using a standardised Excel template. In every template there are user-friendly tabs for entry of data. Key user-entered data elements are then summarised in two Excel tables as follows:

- expt_metadata - experiment-wide data e.g. date of experiment
- rxn_metadata - reaction level data e.g. post-PCR DNA concentration

Originally VBA code in the spreadsheet was used to export individual data tables to csv files. `warehouse` can now directly import, munge and export experimental data as required. 

### Sample data
Sample data can also be pulled into the `visualise` command from a csv file. Curently this requires the following fields: Sample ID, Extraction ID, Date Collected, Parasitaemia (p/ul), and Province.

### Sequence analysis outputs
Finally outputs from sequencing runs can also be pulled into warehouse through the `visualise` command from the standard NOMADS folder structure (outlined below).

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
Usage: warehouse.py [OPTIONS] COMMAND [ARGS]...

  NOMADS Sequencing Data - experimental outputs

Options:
  --help  Show this message and exit.

Commands:
  metadata    Extract, validate and optionally export experimental data
  seqfolders  Create appropriate NOMADS directory structure for a sequencing run
  visualise   Dashboard to visualise summary data from NOMADS assays

```
Each warehouse command also has a --help menu.

## Examples
### metadata
- Extract, validate and output all data into csv files:
```
python scripts/warehouse.py metadata -e example_data/experimental/no_errors/ `
```
OR you can also see errors highlighted as follows:
```
python scripts/warehouse.py metadata -e example_data/experimental/with_errors/`
```

You can also output all of the data to a directory of your choosing as follows:
```
python scripts/warehouse.py metadata -e example_data/experimental/no_errors/ -o experiments/ `
```

### seqfolders
- Create standardised directory hierarchy from a sequencing run for data storage, validate experimental data, and create output files for downstream tools: 
```
python scripts/warehouse.py seqfolders -e example_data/experimental/no_errors -e SLJS034
```
The standard strucure should contain these folders at a minimum:
metadata - sample_info.csv is stored here for downstream tools e.g. nomadic
minknow - raw sequence data should be stored here
nomadic - outputs from nomadic should be stored here

A `.ini` file can be used to define the desired folder structure, including sub-folders (see `resources/seqfolders` for an example), but the default ini produces the above.

### visualise
- View dashboard of all experimental, sample and sequence data available: 
```
python scripts/warehouse.py visualise -e example_data/experimental/no_errors/ -s example_data/seqdata/ -c example_data/sample/sample_metadata.csv 

```
