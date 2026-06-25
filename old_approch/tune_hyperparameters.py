import os
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import mean_squared_error
import optuna
import json
import warnings

warnings.filterwarnings('ignore')

# Paths
DATA_PATH = r"d:\Python-2025\Antigravity\honeywell\03TIC_1023_PVHI\03TIC_1023_PVHI\03TIC_1023_Final_merged_TripDataRemoved.parquet"
MODEL_DIR = r"d:\Python-2025\Antigravity\honeywell\models\v2_tuned"

os.makedirs(MODEL_DIR, exist_ok=True)

def preprocess_and_feature_engineering():
    print("Loading data...")
    df = pd.read_parquet(DATA_PATH)
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
    key_cols = ['03TIC_1023.PV', '03TI_1024.PV', '03TI_1015.PV', '03PIC_1023.PV', '03TI_1081.PV']
    
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

def run_tuning():
    df = preprocess_and_feature_engineering()
    
    # Extract feature list
    exclude_cols = ['target_5m', 'target_15m', 'target_30m', 'target_60m']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Define splits chronologically
    train_end = pd.to_datetime('2024-12-31 23:59:00')
    val_end = pd.to_datetime('2025-06-30 23:59:00')
    
    horizons = [5]
    
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    
    for h in horizons:
        print(f"\n==================================================")
        print(f" Optuna Tuning Study for Horizon: {h} Minutes")
        print(f"==================================================")
        
        target_name = f'target_{h}m'
        
        # Prepare datasets (drop rows where target is NaN)
        data_h = df[feature_cols + [target_name]].dropna(subset=[target_name])
        
        # Chronological splits
        train_data = data_h.loc[:train_end]
        val_data = data_h.loc[train_end + pd.Timedelta(minutes=1):val_end]
        
        # Downsample training and validation sets for 10x faster tuning
        # taking every 8th sample preserves time-series characteristics while reducing row count
        X_train, y_train = train_data[feature_cols].iloc[::8], train_data[target_name].iloc[::8]
        X_val, y_val = val_data[feature_cols].iloc[::8], val_data[target_name].iloc[::8]
        
        print(f"Data shapes (Downsampled) - Train: {X_train.shape}, Val: {X_val.shape}")
        
        def objective(trial):
            params = {
                'n_estimators': 500,
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.15, log=True),
                'num_leaves': trial.suggest_int('num_leaves', 31, 127),
                'max_depth': trial.suggest_int('max_depth', 5, 10),
                'min_child_samples': trial.suggest_int('min_child_samples', 10, 100),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
                'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
                'random_state': 42,
                'n_jobs': -1,
                'verbosity': -1
            }
            
            model = lgb.LGBMRegressor(**params)
            callbacks = [lgb.early_stopping(stopping_rounds=20, verbose=False)]
            
            model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                eval_metric='rmse',
                callbacks=callbacks
            )
            
            val_preds = model.predict(X_val)
            val_rmse = np.sqrt(mean_squared_error(y_val, val_preds))
            return val_rmse

        # Create Optuna study
        study = optuna.create_study(direction="minimize")
        print("Starting optimization trials (15 trials total)...")
        
        study.optimize(objective, n_trials=15, show_progress_bar=True)
        
        print(f"Study finished. Best trial validation RMSE: {study.best_value:.4f}")
        print("Best Hyperparameters:")
        print(json.dumps(study.best_params, indent=2))
        
        # Save best parameters to JSON
        param_path = os.path.join(MODEL_DIR, f"best_params_{h}m.json")
        with open(param_path, "w") as f:
            json.dump(study.best_params, f, indent=2)
        print(f"Saved best parameters to {param_path}")

if __name__ == "__main__":
    run_tuning()
