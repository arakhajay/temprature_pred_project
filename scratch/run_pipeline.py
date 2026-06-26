import os
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.inspection import permutation_importance
import shap
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')

# Paths
FEATURES_PATH = "outputs/new_approach_features.parquet"
OUTPUT_DIR = "outputs/eda_reports"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_complexity(name):
    if name in ['hour', 'month', 'dayofweek']:
        return 1
    elif '_lag_' in name:
        return 2
    elif '_diff_' in name:
        return 3
    elif '_roll_mean_' in name:
        return 4
    elif '_roll_max_' in name or '_roll_min_' in name:
        return 5
    elif '_roll_std_' in name:
        return 6
    else:
        # Raw features
        return 0

def run_feature_selection(df, target_col, horizon_name):
    print(f"\n=== Starting Feature Selection Pipeline for Horizon: {horizon_name} ===")
    
    # Filter target non-null rows
    exclude_cols = ['target_5m', 'target_15m', 'target_30m', 'target_60m']
    feature_cols = [c for c in df.columns if c not in exclude_cols and c != 'TimeStamp']
    
    data_h = df[feature_cols + [target_col]].dropna(subset=[target_col])
    
    # Chronological splits (use Train set for cross-validation)
    train_end = pd.to_datetime('2025-06-12 23:59:00')
    train_data = data_h.loc[:train_end]
    
    # Extract X, y for training
    X = train_data[feature_cols]
    y = train_data[target_col]
    
    # ----------------------------------------------------
    # Phase 1: High-Correlation Filter (Collinearity Removal)
    # ----------------------------------------------------
    print("\n[Phase 1] Calculating Pearson correlation matrix...")
    # Downsample for correlation calculation to save memory and time
    corr_matrix = X.iloc[::5].corr().abs()
    
    # Find highly correlated pairs
    upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    collinear_pairs = []
    for col in upper_tri.columns:
        correlated_with = upper_tri.index[upper_tri[col] > 0.90].tolist()
        for idx in correlated_with:
            collinear_pairs.append((idx, col, upper_tri.loc[idx, col]))
            
    print(f"Found {len(collinear_pairs)} pairs with correlation > 0.90")
    
    # Determine features to drop
    to_drop = set()
    for feat1, feat2, r_val in collinear_pairs:
        if feat1 in to_drop or feat2 in to_drop:
            continue
        # Drop the one with higher complexity score
        comp1 = get_complexity(feat1)
        comp2 = get_complexity(feat2)
        
        if comp1 > comp2:
            to_drop.add(feat1)
            # print(f"Collinear Pair: ({feat1}, {feat2}, r={r_val:.4f}) -> Dropping {feat1} (complexity {comp1} > {comp2})")
        else:
            to_drop.add(feat2)
            # print(f"Collinear Pair: ({feat1}, {feat2}, r={r_val:.4f}) -> Dropping {feat2} (complexity {comp2} > {comp1})")
            
    phase1_features = [c for c in feature_cols if c not in to_drop]
    print(f"Phase 1 complete. Dropped {len(to_drop)} features. Remaining: {len(phase1_features)}")
    
    # ----------------------------------------------------
    # Phase 2: Time-Series Split & Permutation Importance
    # ----------------------------------------------------
    print("\n[Phase 2] Computing Permutation Importance with 5-fold TimeSeriesSplit...")
    tscv = TimeSeriesSplit(n_splits=5)
    
    # We downsample the training set for Permutation Importance calculation to make it fast
    # (Permutation importance shuffles each column, running model predict N_features times per fold)
    X_phase1 = X[phase1_features]
    
    importances = np.zeros(len(phase1_features))
    
    fold = 1
    for train_idx, val_idx in tscv.split(X_phase1):
        # print(f"  Processing Fold {fold}/5...")
        # Downsample within folds to speed up execution
        X_tr, y_tr = X_phase1.iloc[train_idx].iloc[::20], y.iloc[train_idx].iloc[::20]
        X_va, y_va = X_phase1.iloc[val_idx].iloc[::20], y.iloc[val_idx].iloc[::20]
        
        # Train a fast baseline LightGBM Regressor
        model = lgb.LGBMRegressor(
            n_estimators=150,
            learning_rate=0.08,
            num_leaves=31,
            max_depth=6,
            random_state=42,
            n_jobs=-1,
            verbosity=-1
        )
        model.fit(X_tr, y_tr)
        
        # Permutation Importance
        r = permutation_importance(model, X_va, y_va, scoring='neg_mean_absolute_error', n_repeats=3, random_state=42, n_jobs=-1)
        importances += r.importances_mean
        fold += 1
        
    # Average importance
    importances /= tscv.n_splits
    
    # Create importance dataframe
    imp_df = pd.DataFrame({
        'Feature': phase1_features,
        'Importance': importances
    }).sort_values('Importance', ascending=False)
    
    # Filter positive importance features
    positive_imp_df = imp_df[imp_df['Importance'] > 0.0]
    print(f"Features with positive permutation importance: {len(positive_imp_df)}")
    
    # Keep top 25-30 features (let's keep top 25 features)
    top_n = min(25, len(positive_imp_df))
    phase2_features = positive_imp_df.head(top_n)['Feature'].tolist()
    print(f"Phase 2 complete. Selected top {top_n} features: {phase2_features}")
    
    # ----------------------------------------------------
    # Phase 3: SHAP TreeExplainer
    # ----------------------------------------------------
    print("\n[Phase 3] Retraining model on selected features and running SHAP Explainer...")
    val_end = pd.to_datetime('2025-08-09 23:59:00')
    val_data = data_h.loc[train_end + pd.Timedelta(minutes=1):val_end]
    
    X_train_final = train_data[phase2_features]
    y_train_final = train_data[target_col]
    X_val_final = val_data[phase2_features]
    y_val_final = val_data[target_col]
    
    # Train model on selected features
    model_final = lgb.LGBMRegressor(
        n_estimators=300,
        learning_rate=0.05,
        num_leaves=63,
        max_depth=8,
        random_state=42,
        n_jobs=-1,
        verbosity=-1
    )
    model_final.fit(
        X_train_final, y_train_final,
        eval_set=[(X_val_final, y_val_final)],
        callbacks=[lgb.early_stopping(stopping_rounds=20, verbose=False)]
    )
    
    # Calculate SHAP values
    explainer = shap.TreeExplainer(model_final)
    # Downsample validation set for SHAP calculation to make it fast
    X_val_sample = X_val_final.iloc[::20]
    shap_values = explainer(X_val_sample)
    
    # Plot SHAP summary and save
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X_val_sample, show=False)
    plt.title(f"SHAP Feature Importance Summary ({horizon_name})", fontsize=14, fontweight='bold', pad=15)
    plt.tight_layout()
    plot_path = os.path.join(OUTPUT_DIR, f"shap_summary_plot_{horizon_name}.png")
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved SHAP summary plot: {plot_path}")
    
    # Filter features based on mean absolute SHAP value
    # shap_values.values is of shape (N_samples, N_features)
    mean_abs_shaps = np.abs(shap_values.values).mean(axis=0)
    shap_imp_df = pd.DataFrame({
        'Feature': phase2_features,
        'Mean_Abs_SHAP': mean_abs_shaps
    }).sort_values('Mean_Abs_SHAP', ascending=False)
    
    # Save final feature selection report
    csv_path = os.path.join(OUTPUT_DIR, f"selected_features_{horizon_name}.csv")
    shap_imp_df.to_csv(csv_path, index=False)
    print(f"Saved selected features report: {csv_path}")
    
    # Minimal SHAP threshold
    threshold = 1e-4
    final_features = shap_imp_df[shap_imp_df['Mean_Abs_SHAP'] >= threshold]['Feature'].tolist()
    print(f"Final selected features (Mean Abs SHAP >= {threshold}): {len(final_features)}")
    print(final_features)
    
    return final_features

def main():
    print("Loading preprocessed feature matrix...")
    df = pd.read_parquet(FEATURES_PATH)
    df['TimeStamp'] = pd.to_datetime(df['TimeStamp'])
    df = df.set_index('TimeStamp')
    
    # We will do it for the 15-minute horizon first
    final_15m = run_feature_selection(df, 'target_15m', '15m')
    
    # Let's save a global JSON with selected features for all horizons
    # For now, let's run it for all horizons to be thorough!
    selected_features_dict = {'15m': final_15m}
    
    for h in [5, 30, 60]:
        selected_features_dict[f'{h}m'] = run_feature_selection(df, f'target_{h}m', f'{h}m')
        
    import json
    with open("outputs/selected_features_by_horizon.json", "w") as f:
        json.dump(selected_features_dict, f, indent=2)
    print("\n[OK] Saved all selected features to outputs/selected_features_by_horizon.json")

if __name__ == "__main__":
    main()
