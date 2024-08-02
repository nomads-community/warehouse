<p align="center"><img src="misc/warehouse_logo.png" width="500"></p>
## Overview
The idea for this repository is to help streamline and standardise the storage of experimental data generated from NOMADS assays. In particular, we are trying to encourage standardised:
- Experiment names
- Directory hierarchies
- Metadata files

## Experimental Data
All experimental data is produced using a standardised Excel spreadsheets (see the `templates` folder). In every template there are user-friendly tabs for entry of data. Key user-entered data elements are then summarised in two Excel tables as follows:

- expt_metadata - experiment-wide data e.g. date of experiment
- rxn_metadata - reaction level data e.g. post-PCR DNA concentration

Originally VBA code in the spreadsheet was used to export individual data tables to csv files. `warehouse` can now directly import, munge and export experimental data as required. The standardisation that warehouse promotes relies on a number of identifiers:

### Experiment ID
Every experiment is given a unique ID composed of:
- Experiment type (2 letters) e.g. SW (sWGA), PC (PCR), SL (Sequence Library)
- Users initials (2 letters) e.g. Bwalya Kabale would be BW
- Three digit incremental count for each experiment type e.g. 001
The third PCR for Bwalya Kabale would therefore be PCBW003. Most of this is automatically generated through the Excel templates.

### Sample ID
Each sample must have a unique sampleID that can consist of any combination of characters. It is recommended that this should be the 'master' id assigned during sample collection and the reference for any sample metadata collected.

### Extraction ID
It is assumed that every mosquito / blood spot sample will need to have DNA extracted from it before testing. Multiple extractions may be made from a single sample therefore each needs a unique reference. It is recommended that a simple system is adopted to geenrate the extraction ID so that is can be transcribed onto tubes / plates as necessary. NOMADS recommend using a two letter prefix and then number extracts sequentially with three digits e.g. AA001, AA002 etc.

### Reaction ID
To track the movement of samples / extracts through different experiments, a unique identifier is used for each. This is composed of the experiment id and the well or reaction number e.g. the pcr_identifier for the sample tested in well A1 in PCBW003 would be `PCBW003_A1`

## Sample Data
Sample information e.g. date collected, parasitaemia etc should be imported from a csv file with fields defined in an accompanying `.ini` file (see `example_data/sample/`). Only fields entered into the `.ini` file will be accessible.

## Sequence Data
Sequence data generated through `nomadic` and / or `savanna` can be imported to enable multi-experimental comparisons to be made.


## Installation

#### Requirements

To install `warehouse`, you will need:
- Version control software [git](https://github.com/git-guides/install-git)
- Package manager [mamba](https://github.com/conda-forge/miniforge) 

#### Steps

**1. Clone the repository from github:**
```
git clone https://github.com/nomads-community/warehouse
cd warehouse
```

**2. Install the dependencies with mamba:**
```
mamba env create -f environments/run.yml
```

**3. Open the `warehouse` environment:**
```
mamba activate warehouse
```
**4. Install `warehouse` and remaining dependencies:**
```
pip install -e .
```
**5. Test your installation:** In the terminal, you should see available commands by typing:
```
warehouse --help
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
### `metadata`
- Extract, validate and output all data into csv files:
```
warehouse metadata -e example_data/experimental/no_errors/ `
```
OR you can also see errors highlighted as follows:
```
warehouse metadata -e example_data/experimental/with_errors/`
```

You can also output all of the data to a directory of your choosing as follows:
```
warehouse metadata -e example_data/experimental/no_errors/ -o experiments/ `
```

### `seqfolders`
- Create standardised directory hierarchy from a sequencing run for data storage, validate experimental data, and create output files for downstream tools: 
```
warehouse seqfolders -e example_data/experimental/no_errors -e SLJS034
```
The standard strucure should contain these folders at a minimum:
metadata - sample_info.csv is stored here for downstream tools e.g. nomadic
minknow - raw sequence data should be stored here
nomadic - output from `nomadic` should be stored here
savanna - output from `savanna` should be stored here

A `.ini` file can be used to define the desired folder structure, including sub-folders (see `resources/seqfolders` for an example), but the default ini produces the above.

### `visualise`
- View dashboard of all experimental, sample and sequence data available.
```
warehouse visualise -e example_data/experimental/no_errors/ -s example_data/seqdata/ -c example_data/sample/sample_metadata.csv

```
