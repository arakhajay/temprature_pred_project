# Adjust working directory to project root if run from inside new_approch folder
import os
if os.path.basename(os.getcwd()) == 'new_approch':
    os.chdir('..')

import pandas as pd

# Paths
DATA_PATH = r"d:\Python-2025\Antigravity\honeywell\03TIC_1023_PVHI\03TIC_1023_PVHI\03TIC_1023_Final_merged_TripDataRemoved.parquet"
SCENARIO_DIR = r"d:\Python-2025\Antigravity\honeywell\scenarios"

os.makedirs(SCENARIO_DIR, exist_ok=True)

def generate():
    print("Loading main dataset...")
    df = pd.read_parquet(DATA_PATH)
    df['TimeStamp'] = pd.to_datetime(df['TimeStamp'])
    df = df.sort_values('TimeStamp').reset_index(drop=True)
    
    # Target tag
    target_col = '03TIC_1023.PV'
    
    print("Extracting Scenario 1: Critical Thermal Upset (July 17, 2025)...")
    # July 17, 2025 has a 9-hour alarm episode. We slice from 06:00:00 to 22:00:00
    start_date = pd.to_datetime('2025-07-17 06:00:00')
    end_date = pd.to_datetime('2025-07-17 22:00:00')
    
    scenario_1 = df[(df['TimeStamp'] >= start_date) & (df['TimeStamp'] <= end_date)].copy()
    scenario_1 = scenario_1.sort_values('TimeStamp').reset_index(drop=True)
    
    # Save Scenario 1
    sc1_path = os.path.join(SCENARIO_DIR, "upset_event_july_2025.parquet")
    scenario_1.to_parquet(sc1_path)
    print(f"Scenario 1 saved to {sc1_path} (Shape: {scenario_1.shape})")
    
    print("\nExtracting Scenario 2: Normal Stable Operation (May 15, 2025)...")
    # Let's find a normal day. May 15, 2025 06:00:00 to 22:00:00
    start_normal = pd.to_datetime('2025-05-15 06:00:00')
    end_normal = pd.to_datetime('2025-05-15 22:00:00')
    
    scenario_2 = df[(df['TimeStamp'] >= start_normal) & (df['TimeStamp'] <= end_normal)].copy()
    scenario_2 = scenario_2.sort_values('TimeStamp').reset_index(drop=True)
    
    # Verify that it doesn't cross 21.0
    max_temp = scenario_2[target_col].max()
    print(f"Max temperature in Scenario 2: {max_temp:.2f} degC (Threshold is 21.0)")
    
    # Save Scenario 2
    sc2_path = os.path.join(SCENARIO_DIR, "normal_operation.parquet")
    scenario_2.to_parquet(sc2_path)
    print(f"Scenario 2 saved to {sc2_path} (Shape: {scenario_2.shape})")
    print("\nScenario generation completed successfully.")

if __name__ == "__main__":
    generate()
