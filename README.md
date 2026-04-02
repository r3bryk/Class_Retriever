# Class_Retriever.py

## Description

`Class_Retriever.py` is designed to process LECO ChromaTOF GC×GC-MS export files (`.txt`, tab-delimited) and extract summarized information for predefined compound classes such as alkanes, DINCH, and phthalates.

The script groups detected features into chemical classes based on the Classifications column, calculates class-level metrics (e.g., retention time ranges, total normalized area), and exports the results into a structured Excel file for downstream interpretation.

## What does the script do

The script takes tab-separated `TXT` files as input and does the following:

1. Loads input files via GUI selection. A file selection dialog is opened, allowing the user to select one or multiple `.txt` files for processing. Files already containing `_Alk&Phth` in their name are skipped.
2. Detects file encoding automatically. The script reads a portion of each file and determines encoding using `chardet` to ensure proper parsing.
3. Validates and prepares the dataset:

- Removes rows where `Classifications` is empty.
- Ensures `Classifications` values are treated as strings.

4. Applies area cutoff normalization:

- Converts the `Area` column to numeric values.
- Replaces values <18250 (peak area units), NaN, or empty string with -18250 (established cutoff for a specific case; change accordingly).

5. Reclassifies DEHP compounds. Features originally classified as `Phthalate_C8x2` are reassigned to `DEHP` if they meet all of the following criteria:

- RT1 ≈ 3723 ± 8 seconds
- RT2 ≈ 1.323 ± 0.3 seconds
- Base Mass = 149.

6. Splits data into predefined compound classes. The dataset is divided into individual class-specific `DataFrames`, including:

- Alkane series (C10–C36, selected values)
- Phthalates (C8x2–C11x2)
- DINCH (merged from DINCH_HighRT2 and DINCH_LowRT2)
- DEHP (reclassified in the previous step).

7. Processes each class independently. For each class, the script calculates:

- Retention Index (RI) range
- RT1 and RT2 ranges
- Representative chemical formula
- Median base mass
- Total normalized class area
- Representative spectrum (from highest-area feature).

8. Normalizes peak areas using spectral data. For each feature:

- Total spectrum intensity is calculated
- Intensity of the base mass is extracted
- Area is normalized as `Area Total = Area × (Total Spectrum Intensity / Base Mass Intensity)`.

9. Selects representative spectrum. The spectrum corresponding to the highest normalized area within each class is stored as a representative spectrum.
10. Exports results to Excel. Output file is saved as `InitialFilename_Alk&Phth.xlsx`.

## Prerequisites

Before using the script, several applications/tools have to be installed:

1. Visual Studio Code; https://code.visualstudio.com/download.
2. Python 3; https://www.python.org/downloads/windows/.
3. Python Extension in Visual Studio Code > Extensions (`Ctrl + Shift + X`) > Search “python” > Press `Install`.

Then, the required packages, i.e. `pandas`, `chardet`, `openpyxl`, must be installed as follows:
Visual Studio Code > Terminal > New Terminal > In terminal, type `pip install pandas chardet openpyxl` > Press `Enter`.

## How to use the script

To use the script, the following steps must be executed:

1. Run the script:

- Right mouse click anywhere in Visual Studio Code script file > Run Python > Run Python File in Terminal or press `play` button in the top-right corner.

2. Select input files:

- A file dialog window will appear
- Select one or multiple `.txt` files exported from ChromaTOF
- Click `Open`.

3. Processing:

- Each file is processed sequentially
- Progress and QC information are printed to the terminal.

## Notes and recommendations

The input files must contain at least the following columns to be processed: 
`"Name" "R.T. (s)" "Retention Index" "Base Mass" "Area" "Spectrum" "Classifications"`

**NB!**

1. `"Spectrum"` values must be in LECO ChromaTOF format: `39:4500 52:220 67:9999`.
2. `"Classifications"` must contain identifiable class labels such as:

- Alkane_CN, where N is a number in a range 10-36
- Phthalate_CMx2, where M is a number in a range 8-11
- DINCH_HighRT2 and DINCH_LowRT2.

3. `"Base Mass"` must correspond to an `m/z` value present in `"Spectrum"`.

## License

[![MIT License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/license/mit)

Intended for academic and research use.
