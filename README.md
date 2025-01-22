<p align="center"><img src="misc/warehouse_logo.png" width="500"></p>

# Overview
This repository aims to help streamline and standardise the storage of experimental data generated from NOMADS assays. In particular, we are trying to encourage standardised:
- Recording of experimental details
- Storage of sequence data

There are six processes in `warehouse`:
```mermaid
flowchart LR
    subgraph OS1["**Shared drive**"]
    A[<span style="color:orange;">**warehouse templates**</span> 
    Generate group specific templates] --> B[<span style="color:orange;">**warehouse metadata**</span> 
    Record and ensure experimental data is consistent]
    end
    B --> C[<span style="color:orange;">**warehouse seqfolders**</span> 
    Generate sequence data folder for each experiment]
    subgraph SC["**Sequencing computer**"]
        C --> D[<span style="color:orange;">**warehouse aggregate**</span> 
        Aggregate sequence data into sequence data folder]
        D --> E[<span style="color:orange;">**warehouse extract**</span> 
        Extract summary sequence data for wider sharing]
    end
    subgraph OS2["**Shared drive**"]
    E --> T[<span style="color:orange;">**warehouse visualise**</span> 
    View and interact with data in a dashboard]
    end


style OS1 fill:#8a5a67, color: #fefdfd
style OS2 fill:#8a5a67, color: #fefdfd
style SC fill:#678a5a, color: #fefdfd
    
```
Note that steps 3 to 5 must be performed on the sequencing computer, while all others should use the shared online resource. This resource should be sorted into three folders:
- <b>experimental:</b> contains all completed experimental templates
- <b>sample:</b> contains information from the field for samples e.g. date collected, parasitaemia etc, in a spreadsheet or csv, together with a corresponding `.ini` file (see `example_data/sample/`) that defines the different fields
- <b>sequence:</b> - contains summary sequence data extracted from the complete raw sequence data on the sequencing laptop.


## 1. warehouse templates
All experimental data should be recorded in standardised Excel spreadsheets (see `templates` folder). Each has user-friendly tabs for entry of data and an instruction sheet. The standardisation that warehouse promotes relies on a number of identifiers.

<details>
<summary>Identifiers used</summary>

#### Experiment ID
Every experiment is given a unique ID composed of:
- Experiment type (2 letters): e.g. SW (sWGA), PC (PCR), SL (Sequence Library)
- Users initials (2 letters): e.g. Bwalya Kabale would be BW
- Experiment Number (3 digits): Incremental count for each experiment type e.g. 001

The third PCR for Bwalya Kabale would therefore be PCBW003. The templates generate everything except for the experiment number e.g. 001, that is entered by the user.

#### Sample ID
Each sample must have a unique sampleID that can consist of any combination of characters. It is recommended that this should be the 'master' id assigned during sample collection and the reference for any sample metadata collected.

#### Extraction ID
It is assumed that every mosquito / blood spot sample will need to have DNA extracted from it before testing. Multiple extractions may be made from a single sample therefore each needs a unique reference. A simple system should be used to generate the extraction ID so that is can be transcribed onto tubes / plates as necessary. NOMADS recommend using a two letter prefix and then number extracts sequentially with three digits e.g. AA001, AA002 etc.

#### Reaction ID
To track the movement of samples / extracts through different experiments, a unique identifier is used for each. This is composed of the experiment id and the well or reaction number e.g. the `pcr_identifier` for the sample tested in well A1 in PCBW003 would be `PCBW003_A1`
</details>


Templates are regularly improved / updated in this repository. To avoid manual entry of group details every time an update is made, users can populate the latest templates with their group specific details using this command.

<details>
<summary>Example usage</summary>

Get a list of the groups available:
```
warehouse templates -l
```
Update templates with group details:

```
warehouse templates -o ~/NOMADS_Blank_Templates -g UCB
```

</details>

## 2. warehouse metadata
This command allows you to directly import, validate, munge and export all experimental data as required. We recommend regularly (e.g. after each experiment) using this function to ensure your data are valid and consistent.

<details>
<summary>Example usage</summary>

Extract and validate all experimental data from Excel files: 
```
warehouse metadata -e example_data/experimental/`
```
Extract, validate and output all experimental data:
```
warehouse metadata -e example_data/experimental/ -o experiments/ `
```
Extract, validate and output experimental data and sample metadata including sample status:
```
warehouse metadata -e example_data/experimental/ -o experiments/ -m example_data/sample/sample_metadata.xlsx`
```
</details>

## 3. warehouse seqfolders
This command will generate a standardised folder hierarchy for storing sequence data associated with a run. By default it will create the following folders:

- **metadata** - experimental data for each rxn e.g. sampleID, barcode assigned etc
- **minknow** - raw sequence data from ONT minknow
- **nomadic** - output from `nomadic`
- **savanna** - output from `savanna`

<details>
<summary>Example usage</summary>

Create directory structure:
```
warehouse seqfolders -e example_data/experimental/ -i SLJS034
```
An `.ini` file can be used to define the desired folder structure, including sub-folders (see `resources/seqfolders` for an example), but  unless absolutely necessary we recommend using the default.
</details>

## 4. warehouse aggregate
  
This command moves sequence data outputs into the sequence data folder. Default locations for data are:
- **minknow**: /var/lib/minknow/data/
- **nomadic**: ~/git/nomadic/results
- **savanna**: ~/git/savanna/results

<details>
<summary>Example usage</summary>

Aggregate sequence data into the seqfolders structure:
```
warehouse aggregate -s example_data/seqdata/ 
```
Aggregate a specific experiment into the seqfolders structure:
```
warehouse aggregate -s example_data/seqdata/ -i SLJS034
```
If your NOMADS git directory is not in '~/git' provide this to aggregate:
```
warehouse aggregate -s example_data/seqdata/ -g ~/Work/git
```
</details>

## 5. warehouse extract
  
Sharing all raw sequence data would be impractical due to its sheer size. This command selectively extracts data to reduce the size, but enable most downstream analyses.

<details>
<summary>Example usage</summary>

Selectively extract sequence data for sharing:
```
warehouse extract -s example_data/seqdata/ -o ~/GoogleDriveFolder/
```
</details>

## 6. warehouse visualise
This command can be used to analyse the experimental, field and sequence data in one dashboard. 

<details>
<summary>Example usage</summary>

View dashboard of all experimental, sample and sequence data available.
```
warehouse visualise -e example_data/experimental/ -s example_data/seqdata/ -m example_data/sample/sample_metadata.csv
```
</details>


## Installation
<details>
  
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

Each warehouse command also has a `--help` menu.

</details>
