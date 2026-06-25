import os
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
MODEL_DIR_V1 = r"d:\Python-2025\Antigravity\honeywell\models\v1_baseline"
MODEL_DIR_V2 = r"d:\Python-2025\Antigravity\honeywell\models\v2_tuned"
OUTPUT_DIR = r"d:\Python-2025\Antigravity\honeywell\outputs"

os.makedirs(MODEL_DIR_V2, exist_ok=True)

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

def train_and_evaluate_tuned():
    df = preprocess_and_feature_engineering()
    
    # Extract feature list
    exclude_cols = ['target_5m', 'target_15m', 'target_30m', 'target_60m']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Define splits chronologically
    train_end = pd.to_datetime('2024-12-31 23:59:00')
    val_end = pd.to_datetime('2025-06-30 23:59:00')
    
    horizons = [5, 15, 30, 60]
    threshold = 21.0
    
    tuned_results = {}
    baseline_results = {}
    
    # We will accumulate test predictions for comparison saving
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
        # 1. Evaluate Baseline Model (V1)
        # ----------------------------------------------------
        baseline_path = os.path.join(MODEL_DIR_V1, f"lgb_model_{h}m.pkl")
        if os.path.exists(baseline_path):
            print("Loading Baseline Model (V1)...")
            base_model = joblib.load(baseline_path)
            
            base_test_preds = base_model.predict(X_test)
            comparison_preds[f'pred_v1_{h}m'] = pd.Series(base_test_preds, index=X_test.index)
            
            # Metrics
            mae_b = mean_absolute_error(y_test, base_test_preds)
            rmse_b = np.sqrt(mean_squared_error(y_test, base_test_preds))
            
            y_test_alarm_b = (y_test >= threshold).astype(int)
            base_preds_alarm = (base_test_preds >= threshold).astype(int)
            
            prec_b, rec_b, f1_b, _ = precision_recall_fscore_support(y_test_alarm_b, base_preds_alarm, average='binary', zero_division=0)
            tn_b, fp_b, fn_b, tp_b = confusion_matrix(y_test_alarm_b, base_preds_alarm).ravel()
            far_b = fp_b / (fp_b + tn_b) if (fp_b + tn_b) > 0 else 0
            
            baseline_results[h] = {
                'MAE': mae_b, 'RMSE': rmse_b, 'Precision': prec_b, 'Recall': rec_b, 'F1': f1_b, 'FAR': far_b,
                'TP': tp_b, 'FP': fp_b, 'TN': tn_b, 'FN': fn_b
            }
            print(f"  V1 Baseline Metrics on Test Set: F1={f1_b:.2%}, Prec={prec_b:.2%}, Rec={rec_b:.2%}, FAR={far_b:.4%}")
        else:
            print(f"Warning: Baseline model V1 not found at {baseline_path}!")
            
        # ----------------------------------------------------
        # 2. Train Tuned Model (V2)
        # ----------------------------------------------------
        param_path = os.path.join(MODEL_DIR_V2, f"best_params_{h}m.json")
        if os.path.exists(param_path):
            print(f"Loading best parameters from {param_path}...")
            with open(param_path, "r") as f:
                best_params = json.load(f)
                
            print("Training Tuned Model (V2)...")
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
            print(f"  Training completed in {time.time() - start_time:.2f} seconds.")
            
            # Save tuned model
            tuned_model_path = os.path.join(MODEL_DIR_V2, f"lgb_model_{h}m.pkl")
            joblib.dump(tuned_model, tuned_model_path)
            print(f"  Tuned model saved to {tuned_model_path}")
            
            # Predict and evaluate
            tuned_test_preds = tuned_model.predict(X_test)
            comparison_preds[f'pred_v2_{h}m'] = pd.Series(tuned_test_preds, index=X_test.index)
            
            mae_t = mean_absolute_error(y_test, tuned_test_preds)
            rmse_t = np.sqrt(mean_squared_error(y_test, tuned_test_preds))
            
            y_test_alarm_t = (y_test >= threshold).astype(int)
            tuned_preds_alarm = (tuned_test_preds >= threshold).astype(int)
            
            prec_t, rec_t, f1_t, _ = precision_recall_fscore_support(y_test_alarm_t, tuned_preds_alarm, average='binary', zero_division=0)
            tn_t, fp_t, fn_t, tp_t = confusion_matrix(y_test_alarm_t, tuned_preds_alarm).ravel()
            far_t = fp_t / (fp_t + tn_t) if (fp_t + tn_t) > 0 else 0
            
            tuned_results[h] = {
                'MAE': mae_t, 'RMSE': rmse_t, 'Precision': prec_t, 'Recall': rec_t, 'F1': f1_t, 'FAR': far_t,
                'TP': tp_t, 'FP': fp_t, 'TN': tn_t, 'FN': fn_t
            }
            print(f"  V2 Tuned Metrics on Test Set: F1={f1_t:.2%}, Prec={prec_t:.2%}, Rec={rec_t:.2%}, FAR={far_t:.4%}")
        else:
            print(f"Error: Optimal parameters JSON not found at {param_path}!")
            
    # ----------------------------------------------------
    # 3. Create and Save Comparison Summary
    # ----------------------------------------------------
    print("\n=========================================")
    print(" Creating Performance Comparison Summary")
    print("=========================================")
    
    comparison_rows = []
    for h in horizons:
        row_base = {
            'Horizon': f'{h}m',
            'Version': 'V1 Baseline',
            'MAE': baseline_results.get(h, {}).get('MAE', np.nan),
            'RMSE': baseline_results.get(h, {}).get('RMSE', np.nan),
            'Precision': baseline_results.get(h, {}).get('Precision', np.nan),
            'Recall': baseline_results.get(h, {}).get('Recall', np.nan),
            'F1': baseline_results.get(h, {}).get('F1', np.nan),
            'FAR': baseline_results.get(h, {}).get('FAR', np.nan),
            'TP': baseline_results.get(h, {}).get('TP', np.nan),
            'FP': baseline_results.get(h, {}).get('FP', np.nan),
            'TN': baseline_results.get(h, {}).get('TN', np.nan),
            'FN': baseline_results.get(h, {}).get('FN', np.nan),
        }
        row_tuned = {
            'Horizon': f'{h}m',
            'Version': 'V2 Tuned',
            'MAE': tuned_results.get(h, {}).get('MAE', np.nan),
            'RMSE': tuned_results.get(h, {}).get('RMSE', np.nan),
            'Precision': tuned_results.get(h, {}).get('Precision', np.nan),
            'Recall': tuned_results.get(h, {}).get('Recall', np.nan),
            'F1': tuned_results.get(h, {}).get('F1', np.nan),
            'FAR': tuned_results.get(h, {}).get('FAR', np.nan),
            'TP': tuned_results.get(h, {}).get('TP', np.nan),
            'FP': tuned_results.get(h, {}).get('FP', np.nan),
            'TN': tuned_results.get(h, {}).get('TN', np.nan),
            'FN': tuned_results.get(h, {}).get('FN', np.nan),
        }
        comparison_rows.append(row_base)
        comparison_rows.append(row_tuned)
        
    comparison_df = pd.DataFrame(comparison_rows)
    comparison_summary_path = os.path.join(OUTPUT_DIR, "tuning_comparison_summary.csv")
    comparison_df.to_csv(comparison_summary_path, index=False)
    print(f"Saved performance comparison report to {comparison_summary_path}")
    
    # Save combined predictions parquet
    comparison_preds_path = os.path.join(OUTPUT_DIR, "comparison_predictions.parquet")
    comparison_preds.to_parquet(comparison_preds_path)
    print(f"Saved test predictions comparison data to {comparison_preds_path}")

if __name__ == "__main__":
    train_and_evaluate_tuned()
