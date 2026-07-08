# Adjust working directory to project root if run from inside approch_v3 folder
import os
if os.path.basename(os.getcwd()) == 'approch_v3':
    os.chdir('..')

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, precision_recall_fscore_support, confusion_matrix
import joblib
import time

# Paths
DATA_PATH = r"d:\Python-2025\Antigravity\honeywell\03TIC_1023_PVHI\03TIC_1023_PVHI\03TIC_1023_Final_merged_TripDataRemoved.parquet"
MODEL_DIR = r"d:\Python-2025\Antigravity\honeywell\models\first_cut_v3"
OUTPUT_DIR = r"d:\Python-2025\Antigravity\honeywell\outputs\first_cut_v3"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
    
    # Selected key columns based on Feature Selection Strategy:
    # 03TIC_1023.PV (Target)
    # 03TI_1024.PV (Column Bottom Inlet Temp - highly correlated, physical driver)
    # 03PIC_1023.PV (C3 Separator Pressure - highly correlated, physical VLE driver)
    # 03TI_1081.PV (Downstream Cooling Temp - moderately correlated, process feedback)
    # 03TIC_1009.PV (Feed Temperature Controller - moderately correlated, process control)
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

def train_and_evaluate():
    # 1. Feature Engineering
    df = preprocess_and_feature_engineering()
    
    # Extract all features (132 features)
    exclude_cols = ['target_5m', 'target_15m', 'target_30m', 'target_60m']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Save a copy of feature list for diagnostics
    feature_path = os.path.join(OUTPUT_DIR, "feature_names.txt")
    with open(feature_path, "w") as f_out:
        f_out.write("\n".join(feature_cols))
            
    print(f"Total engineered features: {len(feature_cols)}. Saved list to {feature_path}.")
    
    # Define splits chronologically
    train_end = pd.to_datetime('2025-06-12 23:59:00')
    val_end = pd.to_datetime('2025-08-09 23:59:00')
    
    horizons = [5, 15, 30, 60]
    
    results = {}
    test_preds_df = pd.DataFrame(index=df.loc[val_end + pd.Timedelta(minutes=1):].index)
    test_preds_df['actual'] = df.loc[val_end + pd.Timedelta(minutes=1):, '03TIC_1023.PV']
    
    for h in horizons:
        print(f"\n=========================================")
        print(f" Training Model for Horizon: {h} Minutes")
        print(f"=========================================")
        
        target_name = f'target_{h}m'
        
        # Prepare datasets (drop rows where target is NaN)
        data_h = df[feature_cols + [target_name]].dropna(subset=[target_name])
        
        # Chronological splits
        train_data = data_h.loc[:train_end]
        val_data = data_h.loc[train_end + pd.Timedelta(minutes=1):val_end]
        test_data = data_h.loc[val_end + pd.Timedelta(minutes=1):]
        
        X_train, y_train = train_data[feature_cols], train_data[target_name]
        X_val, y_val = val_data[feature_cols], val_data[target_name]
        X_test, y_test = test_data[feature_cols], test_data[target_name]
        
        print(f"Train shape: {X_train.shape}, Val shape: {X_val.shape}, Test shape: {X_test.shape}")
        
        # LightGBM Regressor (First Cut Baseline Model)
        model = lgb.LGBMRegressor(
            n_estimators=1000,
            learning_rate=0.05,
            num_leaves=63,
            max_depth=8,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        
        # Train model with early stopping
        start_time = time.time()
        callbacks = [lgb.early_stopping(stopping_rounds=50, verbose=False)]
        
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            eval_metric='rmse',
            callbacks=callbacks
        )
        
        elapsed = time.time() - start_time
        print(f"Training completed in {elapsed:.2f} seconds.")
        
        # Save model
        model_path = os.path.join(MODEL_DIR, f"lgb_model_{h}m.pkl")
        joblib.dump(model, model_path)
        print(f"Model saved to {model_path}")
        
        # Predictions
        val_preds = model.predict(X_val)
        test_preds = model.predict(X_test)
        
        # Align by index
        test_preds_df[f'pred_{h}m'] = pd.Series(test_preds, index=X_test.index)
        
        # --- Regression Metrics ---
        val_mae = mean_absolute_error(y_val, val_preds)
        val_rmse = np.sqrt(mean_squared_error(y_val, val_preds))
        test_mae = mean_absolute_error(y_test, test_preds)
        test_rmse = np.sqrt(mean_squared_error(y_test, test_preds))
        
        print(f"\n--- Regression Metrics ({h}m) ---")
        print(f"Val MAE: {val_mae:.4f} | Val RMSE: {val_rmse:.4f}")
        print(f"Test MAE: {test_mae:.4f} | Test RMSE: {test_rmse:.4f}")
        
        # --- Classification Metrics (Alarm Threshold = 21.0) ---
        threshold = 21.0
        y_test_alarm = (y_test >= threshold).astype(int)
        test_preds_alarm = (test_preds >= threshold).astype(int)
        
        precision, recall, f1, _ = precision_recall_fscore_support(y_test_alarm, test_preds_alarm, average='binary', zero_division=0)
        tn, fp, fn, tp = confusion_matrix(y_test_alarm, test_preds_alarm).ravel()
        far = fp / (fp + tn) if (fp + tn) > 0 else 0
        
        print(f"--- Alarm Classification Metrics (Threshold={threshold}) ---")
        print(f"Precision: {precision:.4%}")
        print(f"Recall (Sensitivity): {recall:.4%}")
        print(f"F1-Score: {f1:.4%}")
        print(f"False Alarm Rate (FAR): {far:.4%}")
        print(f"Confusion Matrix: TP={tp}, FP={fp}, TN={tn}, FN={fn}")
        
        results[h] = {
            'val_mae': val_mae,
            'val_rmse': val_rmse,
            'test_mae': test_mae,
            'test_rmse': test_rmse,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'far': far,
            'tp': tp,
            'fp': fp,
            'tn': tn,
            'fn': fn
        }
        
    # Save all test predictions to Parquet
    preds_path = os.path.join(OUTPUT_DIR, "test_predictions.parquet")
    test_preds_df.to_parquet(preds_path)
    print(f"\nSaved test predictions to {preds_path}")
    
    # Save results summary to CSV
    summary_df = pd.DataFrame(results).T
    summary_path = os.path.join(OUTPUT_DIR, "model_results_summary.csv")
    summary_df.to_csv(summary_path)
    print(f"Saved results summary to {summary_path}")

if __name__ == "__main__":
    train_and_evaluate()
