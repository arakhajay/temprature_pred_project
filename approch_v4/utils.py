import os
import pandas as pd
import numpy as np
import json
import torch
from torch.utils.data import Dataset
from sklearn.preprocessing import StandardScaler

# Constants
DATA_PATH = r"d:\Python-2025\Antigravity\honeywell\03TIC_1023_PVHI\03TIC_1023_PVHI\03TIC_1023_Final_merged_TripDataRemoved.parquet"
SELECTED_FEATURES_PATH = r"d:\Python-2025\Antigravity\honeywell\outputs\selected_features_by_horizon.json"

def preprocess_and_feature_engineering(data_path=DATA_PATH):
    print("Loading data...")
    df = pd.read_parquet(data_path)
    df['TimeStamp'] = pd.to_datetime(df['TimeStamp'])
    df = df.sort_values('TimeStamp')
    
    # 1. Set TimeStamp as index and reindex to complete 1-minute frequency
    print("Reindexing to regular 1-minute grid...")
    df = df.set_index('TimeStamp')
    full_idx = pd.date_range(start=df.index.min(), end=df.index.max(), freq='1min')
    df = df.reindex(full_idx)
    df.index.name = 'TimeStamp'
    
    # 2. Impute very small gaps (e.g. up to 5 minutes) using forward fill
    print("Imputing small gaps (up to 5 mins)...")
    df = df.ffill(limit=5)
    
    target_col = '03TIC_1023.PV'
    
    # 3. Feature Engineering
    print("Engineering features...")
    key_cols = ['03TIC_1023.PV', '03TI_1024.PV', '03PIC_1023.PV', '03TI_1081.PV', '03TIC_1009.PV']
    
    # Time features
    df['hour'] = df.index.hour
    df['month'] = df.index.month
    df['dayofweek'] = df.index.dayofweek
    
    # Lag features
    print("  Creating lag features...")
    for col in key_cols:
        for lag in [1, 2, 5, 10, 15, 30, 60]:
            df[f'{col}_lag_{lag}'] = df[col].shift(lag)
            
    # Rolling features
    print("  Creating rolling window features...")
    for col in key_cols:
        for window in [10, 30, 60]:
            df[f'{col}_roll_mean_{window}'] = df[col].rolling(window=window, min_periods=int(window*0.8)).mean()
            df[f'{col}_roll_std_{window}'] = df[col].rolling(window=window, min_periods=int(window*0.8)).std()
            df[f'{col}_roll_max_{window}'] = df[col].rolling(window=window, min_periods=int(window*0.8)).max()
            df[f'{col}_roll_min_{window}'] = df[col].rolling(window=window, min_periods=int(window*0.8)).min()

    # Rate of change / Difference features
    print("  Creating rate-of-change features...")
    for col in key_cols:
        for diff in [5, 15, 30]:
            df[f'{col}_diff_{diff}'] = df[col] - df[col].shift(diff)
            
    # 4. Target variables (values in the future)
    print("  Creating future targets...")
    df['target_5m'] = df[target_col].shift(-5)
    df['target_15m'] = df[target_col].shift(-15)
    df['target_30m'] = df[target_col].shift(-30)
    df['target_60m'] = df[target_col].shift(-60)
    
    return df

def get_feature_lists(df):
    """
    Returns feature list configurations.
    All Features: 132 features (excluding target_ columns)
    Selected Features: dictionary mapping horizons to lists, and union of them.
    """
    exclude_cols = ['target_5m', 'target_15m', 'target_30m', 'target_60m']
    all_features = [col for col in df.columns if col not in exclude_cols]
    
    # Load selected features
    with open(SELECTED_FEATURES_PATH, "r") as f:
        selected_features_by_horizon = json.load(f)
        
    # Get union of all selected features for Seq-to-Seq
    union_features = set()
    for h_key, f_list in selected_features_by_horizon.items():
        union_features.update(f_list)
    selected_features_by_horizon['union'] = sorted(list(union_features))
    
    return all_features, selected_features_by_horizon

class TimeSeriesDataset(Dataset):
    """
    Memory-efficient PyTorch Dataset that references scaled numpy arrays.
    """
    def __init__(self, features_np, targets_np, valid_indices, seq_len):
        self.features = features_np
        self.targets = targets_np
        self.valid_indices = valid_indices
        self.seq_len = seq_len

    def __len__(self):
        return len(self.valid_indices)

    def __getitem__(self, idx):
        end_idx = self.valid_indices[idx]
        start_idx = end_idx - self.seq_len + 1
        
        seq_x = self.features[start_idx:end_idx + 1]
        val_y = self.targets[end_idx]
        
        return torch.tensor(seq_x, dtype=torch.float32), torch.tensor(val_y, dtype=torch.float32)

def prepare_split_datasets(df, feature_cols, target_col, seq_len=10, sample_step=1):
    """
    Splits the dataframe chronologically, fits scalers on the training set,
    and returns scaled numpy arrays, valid indices, and scalers.
    """
    train_end = pd.to_datetime('2025-06-12 23:59:00')
    val_end = pd.to_datetime('2025-08-09 23:59:00')
    
    # Identify chronological indices
    train_mask = df.index <= train_end
    val_mask = (df.index > train_end) & (df.index <= val_end)
    test_mask = df.index > val_end
    
    # Fit StandardScaler on train split only
    print("Fitting Scalers on Train Split...")
    scaler_x = StandardScaler()
    scaler_x.fit(df.loc[train_mask, feature_cols].fillna(0.0))
    
    scaler_y = StandardScaler()
    # Reshape target for scaler
    train_y_nonnan = df.loc[train_mask, target_col].dropna().values.reshape(-1, 1)
    if len(train_y_nonnan) > 0:
        scaler_y.fit(train_y_nonnan)
    else:
        scaler_y.fit(df[[target_col]].fillna(0.0)) # Fallback if empty
        
    # Scale full arrays
    features_scaled = scaler_x.transform(df[feature_cols].fillna(0.0))
    targets_scaled = scaler_y.transform(df[[target_col]].fillna(0.0)).flatten()
    
    # Find valid windows (where no NaNs exist in the features window and target is not NaN)
    print("Finding valid windows...")
    valid_features = df[feature_cols].notna().all(axis=1)
    valid_seq = valid_features.rolling(window=seq_len).min() == 1
    valid_target = df[target_col].notna()
    valid_mask = valid_seq & valid_target
    
    # Retrieve indices as integer offsets
    indices = np.arange(len(df))
    train_indices = indices[train_mask & valid_mask]
    val_indices = indices[val_mask & valid_mask]
    test_indices = indices[test_mask & valid_mask]
    
    # Downsample training and validation splits if sample_step > 1 to save time
    if sample_step > 1:
        train_indices = train_indices[::sample_step]
        val_indices = val_indices[::sample_step]
        # Keep test_indices at full resolution to ensure fair and detailed comparison
        
    print(f"Dataset summary: Train size: {len(train_indices)}, Val size: {len(val_indices)}, Test size: {len(test_indices)}")
    
    train_dataset = TimeSeriesDataset(features_scaled, targets_scaled, train_indices, seq_len)
    val_dataset = TimeSeriesDataset(features_scaled, targets_scaled, val_indices, seq_len)
    test_dataset = TimeSeriesDataset(features_scaled, targets_scaled, test_indices, seq_len)
    
    return train_dataset, val_dataset, test_dataset, scaler_x, scaler_y, test_indices
