# Adjust working directory to project root if run from inside approch_v3 folder
import os
if os.path.basename(os.getcwd()) == 'approch_v3':
    os.chdir('..')

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, precision_recall_fscore_support, confusion_matrix
import joblib
import json
import time
import warnings

warnings.filterwarnings('ignore')

# Paths
DATA_PATH = r"d:\Python-2025\Antigravity\honeywell\03TIC_1023_PVHI\03TIC_1023_PVHI\03TIC_1023_Final_merged_TripDataRemoved.parquet"
MODEL_DIR_BASE = r"d:\Python-2025\Antigravity\honeywell\models\first_cut_v3"
MODEL_DIR_TUNED = r"d:\Python-2025\Antigravity\honeywell\models\tuned_v3"
OUTPUT_DIR_TUNED = r"d:\Python-2025\Antigravity\honeywell\outputs\tuned_v3"

os.makedirs(MODEL_DIR_TUNED, exist_ok=True)
os.makedirs(OUTPUT_DIR_TUNED, exist_ok=True)

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

def train_and_evaluate_tuned():
    df = preprocess_and_feature_engineering()
    
    # Extract all features (132 features)
    exclude_cols = ['target_5m', 'target_15m', 'target_30m', 'target_60m']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
        
    # Define splits chronologically
    train_end = pd.to_datetime('2025-06-12 23:59:00')
    val_end = pd.to_datetime('2025-08-09 23:59:00')
    
    horizons = [5, 15, 30, 60]
    threshold = 21.0
    
    comparison_rows = []
    comparison_preds = pd.DataFrame(index=df.loc[val_end + pd.Timedelta(minutes=1):].index)
    comparison_preds['actual'] = df.loc[val_end + pd.Timedelta(minutes=1):, '03TIC_1023.PV']
    
    for h in horizons:
        print(f"\n=========================================")
        print(f" Processing Horizon: {h} Minutes")
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
        
        # ----------------------------------------------------
        # 1. Evaluate First-Cut Baseline Model
        # ----------------------------------------------------
        base_path = os.path.join(MODEL_DIR_BASE, f"lgb_model_{h}m.pkl")
        if os.path.exists(base_path):
            print("Loading First-Cut Baseline Model...")
            base_model = joblib.load(base_path)
            base_test_preds = base_model.predict(X_test)
            comparison_preds[f'pred_base_{h}m'] = pd.Series(base_test_preds, index=X_test.index)
            
            mae_b = mean_absolute_error(y_test, base_test_preds)
            rmse_b = np.sqrt(mean_squared_error(y_test, base_test_preds))
            
            y_test_alarm = (y_test >= threshold).astype(int)
            base_preds_alarm = (base_test_preds >= threshold).astype(int)
            
            prec_b, rec_b, f1_b, _ = precision_recall_fscore_support(y_test_alarm, base_preds_alarm, average='binary', zero_division=0)
            tn_b, fp_b, fn_b, tp_b = confusion_matrix(y_test_alarm, base_preds_alarm).ravel()
            far_b = fp_b / (fp_b + tn_b) if (fp_b + tn_b) > 0 else 0
            
            comparison_rows.append({
                'Horizon': f"{h} Min",
                'Version': 'First-Cut Baseline',
                'F1-Score': f"{f1_b * 100:.2f}%",
                'Precision': f"{prec_b * 100:.2f}%",
                'Recall': f"{rec_b * 100:.2f}%",
                'False Alarm Rate': f"{far_b * 100:.4f}%",
                'MAE (degC)': f"{mae_b:.4f}",
                'RMSE (degC)': f"{rmse_b:.4f}"
            })
            print(f"  Baseline: F1={f1_b:.2%}, Prec={prec_b:.2%}, Rec={rec_b:.2%}, FAR={far_b:.4%}")
        else:
            print(f"Warning: Baseline model not found at {base_path}")
            
        # ----------------------------------------------------
        # 2. Train Tuned Model
        # ----------------------------------------------------
        param_path = os.path.join(MODEL_DIR_TUNED, f"best_params_{h}m.json")
        if os.path.exists(param_path):
            print(f"Loading optimal parameters from {param_path}...")
            with open(param_path, "r") as f:
                best_params = json.load(f)
                
            print("Training Tuned Model...")
            tuned_model = lgb.LGBMRegressor(
                n_estimators=1000,
                random_state=42,
                n_jobs=-1,
                **best_params
            )
            
            callbacks = [lgb.early_stopping(stopping_rounds=50, verbose=False)]
            start_time = time.time()
            tuned_model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                eval_metric='rmse',
                callbacks=callbacks
            )
            print(f"  Tuned model trained in {time.time() - start_time:.2f} seconds.")
            
            # Save tuned model
            tuned_model_path = os.path.join(MODEL_DIR_TUNED, f"lgb_model_{h}m.pkl")
            joblib.dump(tuned_model, tuned_model_path)
            print(f"  Tuned model saved to {tuned_model_path}")
            
            # Predict and Evaluate
            tuned_test_preds = tuned_model.predict(X_test)
            comparison_preds[f'pred_tuned_{h}m'] = pd.Series(tuned_test_preds, index=X_test.index)
            
            mae_t = mean_absolute_error(y_test, tuned_test_preds)
            rmse_t = np.sqrt(mean_squared_error(y_test, tuned_test_preds))
            
            tuned_preds_alarm = (tuned_test_preds >= threshold).astype(int)
            y_test_alarm = (y_test >= threshold).astype(int)
            
            prec_t, rec_t, f1_t, _ = precision_recall_fscore_support(y_test_alarm, tuned_preds_alarm, average='binary', zero_division=0)
            tn_t, fp_t, fn_t, tp_t = confusion_matrix(y_test_alarm, tuned_preds_alarm).ravel()
            far_t = fp_t / (fp_t + tn_t) if (fp_t + tn_t) > 0 else 0
            
            comparison_rows.append({
                'Horizon': f"{h} Min",
                'Version': 'Tuned Model',
                'F1-Score': f"{f1_t * 100:.2f}%",
                'Precision': f"{prec_t * 100:.2f}%",
                'Recall': f"{rec_t * 100:.2f}%",
                'False Alarm Rate': f"{far_t * 100:.4f}%",
                'MAE (degC)': f"{mae_t:.4f}",
                'RMSE (degC)': f"{rmse_t:.4f}"
            })
            print(f"  Tuned: F1={f1_t:.2%}, Prec={prec_t:.2%}, Rec={rec_t:.2%}, FAR={far_t:.4%}")
        else:
            print(f"Error: Parameters JSON not found at {param_path}")
            
    # Save combined predictions Parquet
    preds_path = os.path.join(OUTPUT_DIR_TUNED, "comparison_predictions.parquet")
    comparison_preds.to_parquet(preds_path)
    print(f"\nSaved comparison predictions to {preds_path}")
    
    # Save comparison dataframe
    df_comp = pd.DataFrame(comparison_rows)
    df_comp.to_csv(os.path.join(OUTPUT_DIR_TUNED, "tuning_comparison_summary.csv"), index=False)
    print(f"Saved performance comparison report to outputs/tuned_v3/tuning_comparison_summary.csv")
    print(df_comp)

if __name__ == "__main__":
    train_and_evaluate_tuned()
