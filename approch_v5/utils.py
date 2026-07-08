"""
Approach v5 - Utility Script
Contains data loading, alarm-based chronological splitting, feature engineering, and PyTorch dataset modules.
"""

import os
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset
from sklearn.preprocessing import StandardScaler

# Default raw DCS parquet path
DEFAULT_DATA_PATH = r"d:\Python-2025\Antigravity\honeywell\03TIC_1023_PVHI\03TIC_1023_PVHI\03TIC_1023_Final_merged_TripDataRemoved.parquet"

def load_and_preprocess_data(file_path=DEFAULT_DATA_PATH, target_col="03TIC_1023.PV"):
    """
    Loads raw Parquet/CSV data, reindexes to a regular 1-minute grid, and performs forward-fill imputation.
    
    Args:
        file_path (str): Path to raw Parquet/CSV.
        target_col (str): Target column name.
        
    Returns:
        pd.DataFrame: Cleaned and indexed dataframe.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"DCS Historian dataset not found at: {file_path}")
        
    print("Loading raw historian data...")
    df = pd.read_parquet(file_path)
    
    # Ensure TimeStamp is a datetime object and sort
    if 'TimeStamp' in df.columns:
        df['TimeStamp'] = pd.to_datetime(df['TimeStamp'])
        df = df.sort_values('TimeStamp')
        df = df.set_index('TimeStamp')
    elif not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
    # Reindex to regular 1-minute grid to prevent dynamic alignment errors
    print("Aligning index to uniform 1-minute grid...")
    full_idx = pd.date_range(start=df.index.min(), end=df.index.max(), freq='1min')
    df = df.reindex(full_idx)
    df.index.name = 'TimeStamp'
    
    # Impute small communication dropouts (gaps up to 5 minutes) via forward fill
    print("Applying forward-fill imputation on short gaps (<= 5 mins)...")
    df = df.ffill(limit=5)
    
    return df

def get_alarm_based_split_boundaries(df, target_col="03TIC_1023.PV", threshold=21.0, split_ratio=[0.75, 0.125, 0.125]):
    """
    Computes chronological splitting boundaries (Train/Val/Test) based on alarm episodes.
    Identifies distinct alarm occurrences, counts them, and splits the timeline such that
    75% of alarms go to Train, 12.5% to Val, and 12.5% to Test.
    
    Args:
        df (pd.DataFrame): Input dataframe.
        target_col (str): The column denoting temperature.
        threshold (float): Alarm threshold (e.g., 21.0 degC).
        split_ratio (list): List of ratios [Train, Val, Test].
        
    Returns:
        tuple: (train_end_time, val_end_time) chronological timestamps.
    """
    print(f"Calculating alarm-based chronological splits on threshold {threshold} °C...")
    is_alarm = (df[target_col] >= threshold).astype(int)
    
    # Identify contiguous blocks using diff-cumsum
    alarm_group = (is_alarm == 0).cumsum()
    alarm_periods = df[is_alarm == 1].groupby(alarm_group)
    
    blocks = []
    for _, grp in alarm_periods:
        blocks.append((grp.index.min(), grp.index.max()))
        
    blocks = sorted(blocks, key=lambda x: x[0])
    num_blocks = len(blocks)
    print(f"Detected {num_blocks} unique alarm sequences/episodes.")
    
    if num_blocks == 0:
        # Fallback to standard time splits if no alarms are present
        train_idx = int(len(df) * split_ratio[0])
        val_idx = int(len(df) * (split_ratio[0] + split_ratio[1]))
        return df.index[train_idx], df.index[val_idx]
        
    train_count = int(np.ceil(num_blocks * split_ratio[0]))
    val_count = int(np.ceil(num_blocks * split_ratio[1]))
    
    train_end_idx = train_count - 1
    val_end_idx = train_end_idx + val_count
    
    train_end_time = blocks[train_end_idx][1]
    val_end_time = blocks[min(val_end_idx, num_blocks - 1)][1]
    
    return train_end_time, val_end_time

def engineer_features_pool(df, target_col="03TIC_1023.PV"):
    """
    Expansion Phase: Generates a large pool of candidate features from the base variables.
    
    Args:
        df (pd.DataFrame): Base dataframe.
        target_col (str): Target column.
        
    Returns:
        pd.DataFrame: Expanded feature pool dataframe.
    """
    print("Starting Feature Engineering (Expansion)...")
    df_engineered = df.copy()
    
    # Key columns used for feature engineering
    key_cols = ['03TIC_1023.PV', '03TI_1024.PV', '03PIC_1023.PV', '03TI_1081.PV', '03TIC_1009.PV']
    
    # 1. Cyclical time context features
    df_engineered['hour'] = df_engineered.index.hour
    df_engineered['month'] = df_engineered.index.month
    df_engineered['dayofweek'] = df_engineered.index.dayofweek
    
    # 2. Lag features
    print("  Generating lag features...")
    for col in key_cols:
        for lag in [1, 2, 5, 10, 15, 30, 60]:
            df_engineered[f'{col}_lag_{lag}'] = df_engineered[col].shift(lag)
            
    # 3. Rolling window statistics
    print("  Generating rolling window statistics...")
    for col in key_cols:
        for window in [10, 30, 60]:
            df_engineered[f'{col}_roll_mean_{window}'] = df_engineered[col].rolling(window=window, min_periods=1).mean()
            df_engineered[f'{col}_roll_std_{window}'] = df_engineered[col].rolling(window=window, min_periods=1).std()
            df_engineered[f'{col}_roll_max_{window}'] = df_engineered[col].rolling(window=window, min_periods=1).max()
            df_engineered[f'{col}_roll_min_{window}'] = df_engineered[col].rolling(window=window, min_periods=1).min()
            
    # 4. Expanding window statistics
    print("  Generating expanding statistics...")
    for col in key_cols:
        df_engineered[f'{col}_expanding_mean'] = df_engineered[col].expanding(min_periods=1).mean()
        df_engineered[f'{col}_expanding_max'] = df_engineered[col].expanding(min_periods=1).max()
        
    # 5. Rate-of-change / delta features
    print("  Generating delta rate-of-change features...")
    for col in key_cols:
        for diff in [5, 15, 30]:
            df_engineered[f'{col}_diff_{diff}'] = df_engineered[col] - df_engineered[col].shift(diff)
            
    # 6. Interaction terms
    print("  Generating thermodynamic interaction features...")
    # Product of overhead pressure and bottom temperature (energy balance proxy)
    df_engineered['temp_pressure_product'] = df_engineered['03TIC_1023.PV'] * df_engineered['03PIC_1023.PV']
    # Temperature difference across the column
    df_engineered['temp_delta_bottom_top'] = df_engineered['03TI_1024.PV'] - df_engineered['03TIC_1023.PV']
    
    # Drop rows with NaN due to lag generation to maintain standard windows
    df_engineered = df_engineered.dropna()
    print(f"Feature pool completed. Shape: {df_engineered.shape}")
    return df_engineered

class TimeSeriesDataset(Dataset):
    """
    PyTorch Dataset for standard LSTM single-step or single-horizon training.
    """
    def __init__(self, X, y, window_size=10, horizon=5):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)
        self.window_size = window_size
        self.horizon = horizon

    def __len__(self):
        return len(self.X) - self.window_size - self.horizon + 1

    def __getitem__(self, idx):
        x_seq = self.X[idx : idx + self.window_size]
        y_val = self.y[idx + self.window_size + self.horizon - 1]
        return x_seq, y_val

class Seq2SeqDataset(Dataset):
    """
    PyTorch Dataset for Seq2Seq (Encoder-Decoder) multi-step forecasting (t+1 to t+60).
    """
    def __init__(self, X, y, window_size=10, forecast_size=60):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32)
        self.window_size = window_size
        self.forecast_size = forecast_size

    def __len__(self):
        return len(self.X) - self.window_size - self.forecast_size + 1

    def __getitem__(self, idx):
        x_seq = self.X[idx : idx + self.window_size]
        y_seq = self.y[idx + self.window_size : idx + self.window_size + self.forecast_size]
        last_target = self.y[idx + self.window_size - 1]
        return x_seq, y_seq, last_target
