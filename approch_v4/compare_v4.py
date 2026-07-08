import os
import pandas as pd
import numpy as np

# Paths to all reports
LGB_ALL_PATH = r"outputs/tuned_v3/tuning_comparison_summary.csv"
LGB_SEL_PATH = r"outputs/tuned_new/tuning_comparison_summary.csv"
LSTM_ALL_PATH = r"outputs/lstm_v4/summary_lstm_all.csv"
LSTM_SEL_PATH = r"outputs/lstm_v4/summary_lstm_selected.csv"
SEQ2SEQ_ALL_PATH = r"outputs/seq2seq_v4/summary_seq2seq_all.csv"
SEQ2SEQ_SEL_PATH = r"outputs/seq2seq_v4/summary_seq2seq_selected.csv"

OUTPUT_DIR = r"outputs/v4"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_and_load_summary(path, new_version_name, filter_tuned=True):
    if not os.path.exists(path):
        print(f"Warning: File not found at {path}")
        return None
    df = pd.read_csv(path)
    if filter_tuned:
        df = df[df['Version'] == 'Tuned Model'].copy()
    df['Version'] = new_version_name
    return df

def run_comparison():
    dfs = []
    
    # 1. Load LightGBM All Features
    df_lgb_all = clean_and_load_summary(LGB_ALL_PATH, 'LightGBM (All Features)', filter_tuned=True)
    if df_lgb_all is not None:
        dfs.append(df_lgb_all)
        
    # 2. Load LightGBM Selected Features
    df_lgb_sel = clean_and_load_summary(LGB_SEL_PATH, 'LightGBM (Selected Features)', filter_tuned=True)
    if df_lgb_sel is not None:
        dfs.append(df_lgb_sel)
        
    # 3. Load LSTM All Features
    df_lstm_all = clean_and_load_summary(LSTM_ALL_PATH, 'LSTM (All Features)', filter_tuned=False)
    if df_lstm_all is not None:
        dfs.append(df_lstm_all)
        
    # 4. Load LSTM Selected Features
    df_lstm_sel = clean_and_load_summary(LSTM_SEL_PATH, 'LSTM (Selected Features)', filter_tuned=False)
    if df_lstm_sel is not None:
        dfs.append(df_lstm_sel)
        
    # 5. Load Seq-to-Seq All Features
    df_seq_all = clean_and_load_summary(SEQ2SEQ_ALL_PATH, 'Seq2Seq (All Features)', filter_tuned=False)
    if df_seq_all is not None:
        dfs.append(df_seq_all)
        
    # 6. Load Seq-to-Seq Selected Features
    df_seq_sel = clean_and_load_summary(SEQ2SEQ_SEL_PATH, 'Seq2Seq (Selected Features)', filter_tuned=False)
    if df_seq_sel is not None:
        dfs.append(df_seq_sel)
        
    if not dfs:
        print("Error: No performance summaries could be loaded.")
        return
        
    # Concatenate all
    merged = pd.concat(dfs, ignore_index=True)
    
    # Helper to sort by Horizon numerically
    horizon_order = {
        '5 Min': 5,
        '15 Min': 15,
        '30 Min': 30,
        '60 Min': 60
    }
    merged['Horizon_Num'] = merged['Horizon'].map(horizon_order)
    
    # Define Version order for easy visual comparison
    version_order = {
        'LightGBM (All Features)': 0,
        'LightGBM (Selected Features)': 1,
        'LSTM (All Features)': 2,
        'LSTM (Selected Features)': 3,
        'Seq2Seq (All Features)': 4,
        'Seq2Seq (Selected Features)': 5
    }
    merged['Version_Num'] = merged['Version'].map(version_order)
    
    # Sort
    merged = merged.sort_values(by=['Horizon_Num', 'Version_Num']).drop(columns=['Horizon_Num', 'Version_Num'])
    
    # Save comparison CSV
    comp_path = os.path.join(OUTPUT_DIR, "approach_v4_comparison.csv")
    merged.to_csv(comp_path, index=False)
    print(f"\nSaved approach v4 consolidated comparison report to {comp_path}")
    
    print("\n==========================================================================================")
    print("                      CONSOLIDATED TEMPERATURE ALARM PREDICTION COMPARISON")
    print("==========================================================================================")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(merged.to_string(index=False))
    
    # Save a Markdown table version for artifacts and walkthroughs
    md_table = merged.to_markdown(index=False)
    md_path = os.path.join(OUTPUT_DIR, "approach_v4_comparison.md")
    with open(md_path, "w") as f:
        f.write("# Approach v4 Comparison Table\n\n")
        f.write(md_table)
        f.write("\n")
    print(f"Saved Markdown table to {md_path}")

if __name__ == "__main__":
    run_comparison()
