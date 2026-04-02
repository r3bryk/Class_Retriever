import pandas as pd
import glob
import time
import os
import sys
import warnings
import tkinter as tk
import tkinter.filedialog
from tkinter.filedialog import askopenfilenames
from datetime import datetime
import chardet

# Suppress SettingWithCopyWarning
from pandas.errors import SettingWithCopyWarning
warnings.simplefilter(action='ignore', category=SettingWithCopyWarning)

# Helper function to detect input file encoding
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw = f.read(500000)
    enc = chardet.detect(raw)
    print("Detected encoding:", enc)
    print(150 * "-")
    return enc["encoding"]

# Process classes
def process_class_df(class_df, class_name):
    # RI Range
    ri_min = round(class_df['Retention Index'].min(), 1)
    ri_max = round(class_df['Retention Index'].max(), 1)
    ri_range = f"{ri_min} - {ri_max}"

    # RT1 and RT2 Range
    rt1_values = class_df['R.T. (s)'].apply(lambda x: round(float(x.split(',')[0]), 1) if isinstance(x, str) else float('nan'))
    rt2_values = class_df['R.T. (s)'].apply(lambda x: round(float(x.split(',')[1]), 3) if isinstance(x, str) else float('nan'))
    rt1_range = f"{rt1_values.min()} - {rt1_values.max()}"
    rt2_range = f"{rt2_values.min()} - {rt2_values.max()}"

    # Formula
    if 'Alkane' in class_name:
        c_number = class_name.split('_')[1][1:]
        formula = f"C{c_number}H{int(c_number)*2+2}"
    elif 'DINCH' in class_name:
        formula = 'NA'
    else:
        formulas = {
            'Phthalate_C8x2': 'C24H38O4',
            'Phthalate_C9x2': 'C26H42O4',
            'Phthalate_C10x2': 'C28H46O4',
            'Phthalate_C11x2': 'C30H50O4',
            'DEHP': 'C24H38O4'
        }
        formula = formulas[class_name]

    # Total class area calculation and spectrum (highest area) retrieval
    class_df.loc[:, 'Total Intensity'] = class_df['Spectrum'].apply(lambda x: sum([float(i.split(':')[1]) for i in x.split()]) if isinstance(x, str) else float('nan'))
    class_df.loc[:, 'Base Mass Intensity'] = class_df.apply(lambda row: next((float(i.split(':')[1]) for i in row['Spectrum'].split() if str(int(row['Base Mass'])) + '.' in i.split(':')[0]), float('nan')) if isinstance(row['Spectrum'], str) and row['Base Mass'] else float('nan'), axis=1)
    class_df.loc[:, 'Area Total'] = class_df.apply(lambda row: row['Area'] * row['Total Intensity'] / row['Base Mass Intensity'] if row['Base Mass Intensity'] else float('nan'), axis=1)
    spectrum_highest_area = class_df.loc[class_df['Area Total'].idxmax()]['Spectrum'] if not class_df['Area Total'].isna().all() else 'N/A'

    # Base Mass (median for the class)
    base_mass = round(class_df['Base Mass'].median(), 2)

    # Class Total Area
    class_total_area = class_df['Area Total'].sum().round(0) # Round to integer

    # QC Printing
    print(f"Calculated total class area for {class_name}:")
    print(class_df[['Area Total']])
    print(150 * "-")
    print(f"Total class area for {class_name}: {class_total_area}")
    print(150 * "-")
    print(f"Highest area for {class_name}: {class_df['Area Total'].max()}")
    print(f"Corresponding spectrum (highest area): {spectrum_highest_area}")
    print(150 * "-")

    return pd.DataFrame({
        'Class Name': [class_name],
        'RI Range': [ri_range],
        'RT1 Range (s)': [rt1_range],
        'RT2 Range (s)': [rt2_range],
        'Formula': [formula],
        'Base Mass': [base_mass],
        'Class Total Area': [class_total_area],
        'Spectrum (Highest Area)': [spectrum_highest_area],
        'Samples': ['']
    })

def process_file(filename):
    start_time = time.time()
    print(150 * "-")
    print(f"Processing file: {filename} at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(150 * "-")

    try:
        enc = detect_encoding(filename)
        df = pd.read_csv(filename, delimiter='\t', encoding=enc, on_bad_lines='skip')

        # Create an empty dataframe for output
        columns = ['Class Name', 'RI Range', 'RT1 Range (s)', 'RT2 Range (s)', 'Formula', 'Base Mass', 'Class Total Area', 'Spectrum (Highest Area)']
        df_out = pd.DataFrame(columns=columns)

        # Define unique classifications
        classifications = ['Alkane_C10', 'Alkane_C11', 'Alkane_C12', 'Alkane_C13', 'Alkane_C14', 'Alkane_C15', 'Alkane_C16', 'Alkane_C17', 'Alkane_C18', 'Alkane_C19', 'Alkane_C20', 'Alkane_C21', 'Alkane_C22', 'Alkane_C23', 'Alkane_C24', 'Alkane_C26', 'Alkane_C27', 'Alkane_C28', 'Alkane_C29', 'Alkane_C30', 'Alkane_C31', 'Alkane_C32', 'Alkane_C33', 'Alkane_C34', 'Alkane_C35', 'Alkane_C36', 'Phthalate_C8x2', 'Phthalate_C9x2', 'Phthalate_C10x2', 'Phthalate_C11x2']

        # Drop rows with missing values in 'Classifications' column
        df = df.dropna(subset=['Classifications'])
        # Ensure 'Classifications' values are strings not numbers
        df['Classifications'] = df['Classifications'].astype(str)

        # Replace Areas < Cutoff with -Cutoff
        sample_start_idx = df.columns.get_loc('Area') # Peak area column
        print(f"Sample peak area column is: index {sample_start_idx} 'Area'.")
        print(" ")

        # sample_cols = df.columns[sample_start_idx]
        sample_cols = ['Area']

        def replace_small_areas(df, sample_cols, cutoff):
            print(f"Replacing area values < cutoff (including 0 & NA) with -cutoff...", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            for col in sample_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce') # Convert to numeric, coercing 'NA', 'na', 'N/A', '' to NaN
                condition = (df[col] < cutoff) | (df[col].isna()) # TRUE for all values < cutoff, incl. NaN (NaN < cutoff is FALSE - handled separately)
                df.loc[condition, col] = -cutoff
            print("Area values replacement completed.", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            print(150 * "-")
            return df

        # Cutoff value selection
        cutoff = 18250
        print(f"Using custom cutoff: {int(cutoff)}")
        print(150 * "-")

        # Use the function
        df = replace_small_areas(df, sample_cols, cutoff)

        # Identify and reclassify DEHP based on RT1, RT2, Base Mass
        def is_dehp(row):
            try:
                rt1, rt2 = map(float, row['R.T. (s)'].split(','))
                base_mass = int(row['Base Mass'])
                return (abs(rt1 - 3723) <= 8) and (abs(rt2 - 1.323) <= 0.3) and (base_mass == 149) and ('Phthalate_C8x2' in row['Classifications'])
            except:
                return False

        df.loc[df.apply(is_dehp, axis=1), 'Classifications'] = 'DEHP'

        # Create empty dataframes for each class
        class_dfs = {class_name: pd.DataFrame(columns=df.columns) for class_name in classifications}
        class_dfs['DINCH'] = pd.DataFrame(columns=df.columns)  # Add merged DINCH class
        class_dfs['DEHP'] = pd.DataFrame(columns=df.columns)   # Add DEHP class

        # Populate class dataframes
        for class_name in classifications:
            if class_name == 'Phthalate_C8x2':
                # Exclude any DEHP-labeled rows from this class
                class_dfs[class_name] = df[df['Classifications'].astype(str).str.contains(class_name, na=False) & ~df['Classifications'].astype(str).str.contains('DEHP', na=False)]
            else:
                class_dfs[class_name] = df[df['Classifications'].astype(str).str.contains(class_name, na=False)]

        # Special handling for DINCH class
        dinch_mask = df['Classifications'].astype(str).str.contains('DINCH_HighRT2', na=False) | df['Classifications'].astype(str).str.contains('DINCH_LowRT2', na=False)
        class_dfs['DINCH'] = df[dinch_mask]

        # Special handling for DEHP class
        class_dfs['DEHP'] = df[df['Classifications'].astype(str).str.contains('DEHP', na=False)]

        # Print class dataframes for QC
        for class_name, class_df in class_dfs.items():
            print(f"DataFrame for {class_name}:")
            print(class_df)
            print(150 * "-")

        # Process each class dataframe
        for class_name, class_df in class_dfs.items():
            if not class_df.empty:
                df_out = pd.concat([df_out, process_class_df(class_df, class_name)], ignore_index=True)
                print(f"Processed class: {class_name}")
                print(150 * "-")

        # Print output dataframe for QC
        print("Output DataFrame:")
        print(df_out)
        print(150 * "-")

        # Save the output file
        output_file_path = filename.replace('.txt', '_Alk&Phth.xlsx')
        df_out.to_excel(output_file_path, index=False)
        print(f"Saved processed file: \n{output_file_path}")
        print(150 * "-")

    except Exception as e:
        print(150 * "!")
        print(f'File {os.path.basename(filename)}: Oops! Something went wrong. Error: {e}')
        print(150 * "!")
        sys.exit(f'File {os.path.basename(filename)}: Oops! Something went wrong. Error: {e}')

    end_time = time.time()
    print(f"Time spent processing {filename}: {end_time - start_time} seconds")
    print(150 * "-")

def process_batch():
    batch_start_time = time.time()
    print(" ")
    print(150 * "*")
    print(f"Batch processing started at {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Calling the input TXT file(s) loading dialog
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    inFilenames = tkinter.filedialog.askopenfilenames(defaultextension='.txt', filetypes=[('TXT file', '.txt')], title='Select files for processing...')

    if len(inFilenames) > 0:
        for name in inFilenames:
            if "_Alk&Phth" not in name:
                process_file(name)
                print(150 * "*")
                print('Success! Sample:', os.path.basename(name))
                print(150 * "*")
    else:
        sys.exit('Oops! No files selected.')  # Exiting the script in case no files were selected
    batch_end_time = time.time()
    print(f"Batch processing ended at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total time spent processing batch: {int(batch_end_time - batch_start_time)} seconds")
    print(150 * "*")
    print(150 * "*")

if __name__ == "__main__":
    process_batch()
