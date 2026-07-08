# Adjust working directory to project root if run from inside approch_v3 folder
import os
if os.path.basename(os.getcwd()) == 'approch_v3':
    os.chdir('..')

import pandas as pd
import numpy as np

# Paths
PATH_SELECTED = r"outputs/tuned_new/tuning_comparison_summary.csv"
PATH_ALL_FEATURES = r"outputs/tuned_v3/tuning_comparison_summary.csv"
OUTPUT_DIR = r"outputs/tuned_v3"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def compare():
    print("Loading Selected Features metrics...")
    if not os.path.exists(PATH_SELECTED):
        print(f"Error: Selected Features metrics CSV not found at {PATH_SELECTED}")
        return
        
    df_sel = pd.read_csv(PATH_SELECTED)
    
    print("Loading All Features (v3) metrics...")
    if not os.path.exists(PATH_ALL_FEATURES):
        print(f"Error: All Features metrics CSV not found at {PATH_ALL_FEATURES}")
        return
        
    df_all = pd.read_csv(PATH_ALL_FEATURES)
    
    # Rename columns to distinguish
    df_sel = df_sel.rename(columns={
        'F1-Score': 'F1_Selected',
        'Precision': 'Precision_Selected',
        'Recall': 'Recall_Selected',
        'False Alarm Rate': 'FAR_Selected',
        'MAE (degC)': 'MAE_Selected',
        'RMSE (degC)': 'RMSE_Selected'
    })
    
    df_all = df_all.rename(columns={
        'F1-Score': 'F1_AllFeatures',
        'Precision': 'Precision_AllFeatures',
        'Recall': 'Recall_AllFeatures',
        'False Alarm Rate': 'FAR_AllFeatures',
        'MAE (degC)': 'MAE_AllFeatures',
        'RMSE (degC)': 'RMSE_AllFeatures'
    })
    
    # Merge on Horizon and Version
    merged = pd.merge(df_sel, df_all, on=['Horizon', 'Version'])
    
    # Helper to convert percentage strings back to floats
    def pct_to_float(val):
        if isinstance(val, str):
            return float(val.replace('%', '')) / 100.0
        return val
        
    # Columns to convert
    pct_cols = ['F1_Selected', 'Precision_Selected', 'Recall_Selected', 'FAR_Selected',
                'F1_AllFeatures', 'Precision_AllFeatures', 'Recall_AllFeatures', 'FAR_AllFeatures']
    
    for col in pct_cols:
        merged[col] = merged[col].apply(pct_to_float)
        
    # Calculate differences (All Features - Selected Features)
    merged['Diff_F1 (%)'] = (merged['F1_AllFeatures'] - merged['F1_Selected']) * 100.0
    merged['Diff_Precision (%)'] = (merged['Precision_AllFeatures'] - merged['Precision_Selected']) * 100.0
    merged['Diff_Recall (%)'] = (merged['Recall_AllFeatures'] - merged['Recall_Selected']) * 100.0
    merged['Diff_FAR (%)'] = (merged['FAR_AllFeatures'] - merged['FAR_Selected']) * 100.0
    merged['Diff_MAE (degC)'] = merged['MAE_AllFeatures'] - merged['MAE_Selected']
    merged['Diff_RMSE (degC)'] = merged['RMSE_AllFeatures'] - merged['RMSE_Selected']
    
    # Format percentages back to strings for display and save
    display_cols = ['Horizon', 'Version', 
                    'F1_Selected', 'F1_AllFeatures', 'Diff_F1 (%)',
                    'Precision_Selected', 'Precision_AllFeatures', 'Diff_Precision (%)',
                    'Recall_Selected', 'Recall_AllFeatures', 'Diff_Recall (%)',
                    'FAR_Selected', 'FAR_AllFeatures', 'Diff_FAR (%)',
                    'MAE_Selected', 'MAE_AllFeatures', 'Diff_MAE (degC)',
                    'RMSE_Selected', 'RMSE_AllFeatures', 'Diff_RMSE (degC)']
    
    df_display = merged[display_cols].copy()
    
    # Save comparison CSV
    comparison_csv_path = os.path.join(OUTPUT_DIR, "comparison_selected_vs_all_features.csv")
    df_display.to_csv(comparison_csv_path, index=False)
    print(f"\nSaved comparison report to {comparison_csv_path}")
    
    # Format values for pretty console printing
    for col in ['F1_Selected', 'F1_AllFeatures', 'Precision_Selected', 'Precision_AllFeatures', 'Recall_Selected', 'Recall_AllFeatures']:
        df_display[col] = df_display[col].apply(lambda x: f"{x * 100.0:.2f}%")
        
    for col in ['FAR_Selected', 'FAR_AllFeatures']:
        df_display[col] = df_display[col].apply(lambda x: f"{x * 100.0:.4f}%")
        
    for col in ['Diff_F1 (%)', 'Diff_Precision (%)', 'Diff_Recall (%)', 'Diff_FAR (%)']:
        df_display[col] = df_display[col].apply(lambda x: f"{x:+.2f}%" if x != 0 else "0.00%")
        
    for col in ['Diff_MAE (degC)', 'Diff_RMSE (degC)']:
        df_display[col] = df_display[col].apply(lambda x: f"{x:+.4f}" if x != 0 else "0.0000")
        
    print("\n=========================================================================")
    print("            Model Comparison: Selected Features vs. All Features")
    print("=========================================================================")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(df_display)
    
if __name__ == "__main__":
    compare()
