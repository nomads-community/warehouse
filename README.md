<p align="center"><img src="misc/warehouse_logo.png" width="500"></p>

# Overview
This repository aims to streamline and standardize the storage and recording of experimental details and sequence data generated from NOMADS assays.

# Key Concepts

<details>

### Templates
`warehouse` relies on experimental data being recorded in standardised Excel spreadsheets. Each has an instruction sheet. We recommend opening templates in Excel whenever possible and always starting with a fresh, blank template.

### Experiment ID
Every experiment requires a unique ID that is composed of:
- Experiment type (2 letters): e.g., SW (sWGA), PC (PCR), SL (Sequence Library)
- Users initials (2 letters): e.g., Bwalya Kabale would be BW
- Experiment Number (3 digits): An incremental count for each experiment type for each user (e.g., 001)

The third PCR for Bwalya Kabale would therefore be PCBW003, similarly the third PCR for James Ubuntu would be PCJU003. The templates automatically generate the experiment ID components, with the exception of the 3-digit experiment number (e.g., 001), which is entered by the user.

### Shared Data
A cloud synchronised folder with three subfolders:
    - **experimental:** Contains all completed experimental templates
    - **sample:** Contains one or more sample metadata information sheets, together with a corresponding `.yml` file that defines the fields
    - **sequence:** - contains summary sequence data

### Sequencing laptop
All data generated during a sequencing run should be stored in a single folder on the sequencing laptop. `warehouse` oversees this process.

</details>

# Running `warehouse` 

### 1. `warehouse configure`
To eliminate repetitive entry of the same details, `warehouse configure` can be used to enter all of the required information, e.g., folder locations, for other commands to run without any additional input. This command only needs to be run once on each laptop that `warehouse` is installed on.

<details>

<summary>Example usage</summary>

```
warehouse configure -d GDrive/data -n NMEC -s Sequence_Folder
```

</details>


### 2. `warehouse process`
This command sequentially processes the data using the configured , without any additional input, as follows:
1. Import, check and validate all experimental templates
2. Create a standardised folder hierarchy for each experiment 
3. Aggregate all sequencing outputs into the standard folder hierarchy
4. Extract summary sequence data to share on the cloud
5. Launch interactive user dashboard to view all data

### 3. `warehouse backup`
This command will backup your raw sequence data to an external USB hard disk drive. When you connect your drive, find the path to the drive in your file manager and copy the location for the -b flag
<details>
<summary>Example usage</summary>

```
warehouse backup -b /media/usb_drive/seqdata/
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
