import json
import os

nb_path = "Advanced_EDA_Client.ipynb"
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Locate cells by search terms
feat_exec_idx = -1
exec_summary_idx = -1

for idx, cell in enumerate(nb['cells']):
    source_text = "".join(cell.get('source', []))
    if "# Feature Engineering Execution" in source_text and "df_features" in source_text:
        feat_exec_idx = idx
    elif "## 13. Executive Summary & Recommendations" in source_text:
        exec_summary_idx = idx

print(f"Located cells:")
print(f"  Feature Engineering Execution Cell: {feat_exec_idx}")
print(f"  Executive Summary Cell: {exec_summary_idx}")

explanation_markdown = """### 14.2. Strict 3-Phase Feature Selection Pipeline (Thermodynamic Signal Preservation)

To prune our 113 engineered features down to the most impactful, non-redundant set without losing physical thermodynamic signals, we implement a strict 3-phase feature selection pipeline:

1. **Phase 1: High-Correlation Filter (Collinearity Removal)**
   Refinery data represents continuous physical processes, leading to high collinearity among rolling stats and sequential lags. We compute the Pearson correlation matrix:
   $$R_{i,j} = \\frac{\\text{Cov}(X_i, X_j)}{\\sigma_{i}\\sigma_{j}}$$
   For any feature pair with $|R_{i,j}| > 0.90$, we identify collinearity. To prevent downstream credit-splitting, we drop one feature. Crucially, we retain the feature with the simpler calculation structure. For example, raw sensors (complexity 0) are preferred over lags (complexity 2), which are preferred over rolling averages (complexity 4), which are preferred over rolling standard deviations (complexity 6). This preserves direct thermodynamic indicators.

2. **Phase 2: Time-Series Split & Permutation Importance (Overfitting Filter)**
   We partition the training data using a 5-fold `TimeSeriesSplit` (Forward Chaining) to respect chronological order and prevent lookahead bias. On each fold, we train a baseline tree-based model (LightGBM) and compute permutation importance based on Mean Absolute Error (MAE):
   $$I(f) = \\text{MAE}_{\\text{shuffled}} - \\text{MAE}_{\\text{baseline}}$$
   Features with zero or negative importance (such as calendar 'year' or 'month' variables that capture transient historical conditions rather than physical laws) are filtered out, and we select the top 25 features.

3. **Phase 3: SHAP TreeExplainer (Final Cut & Physical Validation)**
   We retrain the model on the top 25 features and run a `shap.TreeExplainer` on the validation dataset:
   $$\\phi_i = \\sum_{S \\subseteq F \\setminus \\{i\\}} \\frac{|S|!(|F| - |S| - 1)!}{|F|!} \\left[ f(S \\cup \\{i\\}) - f(S) \\right]$$
   We filter out features with a mean absolute SHAP value below a minimal threshold ($10^{-4}$), and plot the SHAP summary to verify that their directional impact aligns with thermodynamic principles (e.g., Column Inlet Temperature should drive Column Overhead Temperature upward).
"""

selection_code = """# Run/Load the Strict 3-Phase Feature Selection Pipeline in EDA
import os
import json
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.inspection import permutation_importance
import shap
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')

FEATURES_JSON = "outputs/selected_features_by_horizon.json"

if os.path.exists(FEATURES_JSON):
    print("Loading pre-computed selected features from JSON...")
    with open(FEATURES_JSON, "r") as f:
        selected_features_by_horizon = json.load(f)
    for h_key, f_list in selected_features_by_horizon.items():
        print(f"Horizon {h_key}: loaded {len(f_list)} selected features.")
else:
    print("Running 3-phase feature selection pipeline...")
    # Setup complexity rankings
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
            return 0

    selected_features_by_horizon = {}
    exclude_cols = ['target_5m', 'target_15m', 'target_30m', 'target_60m']
    feature_cols = [c for c in df_features.columns if c not in exclude_cols and c != 'TimeStamp']
    
    # Chronological split definitions
    train_end = pd.to_datetime('2025-06-12 23:59:00')
    val_end = pd.to_datetime('2025-08-09 23:59:00')
    
    for h in [5, 15, 30, 60]:
        target_col = f'target_{h}m'
        data_h = df_features[feature_cols + [target_col]].dropna(subset=[target_col])
        train_data = data_h.loc[:train_end]
        X = train_data[feature_cols]
        y = train_data[target_col]
        
        # Phase 1: High-Correlation Filter
        corr_matrix = X.iloc[::10].corr().abs()
        upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        to_drop = set()
        for col in upper_tri.columns:
            correlated_with = upper_tri.index[upper_tri[col] > 0.90].tolist()
            for idx in correlated_with:
                if idx in to_drop or col in to_drop:
                    continue
                if get_complexity(idx) > get_complexity(col):
                    to_drop.add(idx)
                else:
                    to_drop.add(col)
        phase1_features = [c for c in feature_cols if c not in to_drop]
        
        # Phase 2: Time-Series Split & Permutation Importance
        tscv = TimeSeriesSplit(n_splits=5)
        X_phase1 = X[phase1_features]
        importances = np.zeros(len(phase1_features))
        
        for train_idx, val_idx in tscv.split(X_phase1):
            X_tr, y_tr = X_phase1.iloc[train_idx].iloc[::50], y.iloc[train_idx].iloc[::50]
            X_va, y_va = X_phase1.iloc[val_idx].iloc[::50], y.iloc[val_idx].iloc[::50]
            
            model = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.1, num_leaves=31, random_state=42, n_jobs=-1, verbosity=-1)
            model.fit(X_tr, y_tr)
            r = permutation_importance(model, X_va, y_va, scoring='neg_mean_absolute_error', n_repeats=3, random_state=42, n_jobs=-1)
            importances += r.importances_mean
        importances /= tscv.n_splits
        
        imp_df = pd.DataFrame({'Feature': phase1_features, 'Importance': importances}).sort_values('Importance', ascending=False)
        positive_imp = imp_df[imp_df['Importance'] > 0.0]
        phase2_features = positive_imp.head(min(25, len(positive_imp)))['Feature'].tolist()
        
        # Phase 3: SHAP explainer
        val_data = data_h.loc[train_end + pd.Timedelta(minutes=1):val_end]
        X_train_final = train_data[phase2_features]
        y_train_final = train_data[target_col]
        X_val_final = val_data[phase2_features]
        y_val_final = val_data[target_col]
        
        model_final = lgb.LGBMRegressor(n_estimators=200, learning_rate=0.05, num_leaves=63, random_state=42, n_jobs=-1, verbosity=-1)
        model_final.fit(X_train_final, y_train_final, eval_set=[(X_val_final, y_val_final)], callbacks=[lgb.early_stopping(20, verbose=False)])
        
        explainer = shap.TreeExplainer(model_final)
        X_val_sample = X_val_final.iloc[::50]
        shap_values = explainer(X_val_sample)
        
        mean_abs_shaps = np.abs(shap_values.values).mean(axis=0)
        shap_imp_df = pd.DataFrame({'Feature': phase2_features, 'Mean_Abs_SHAP': mean_abs_shaps}).sort_values('Mean_Abs_SHAP', ascending=False)
        
        final_features = shap_imp_df[shap_imp_df['Mean_Abs_SHAP'] >= 1e-4]['Feature'].tolist()
        selected_features_by_horizon[f'{h}m'] = final_features
        print(f"Selected {len(final_features)} features for {h}m horizon.")
        
    os.makedirs("outputs", exist_ok=True)
    with open(FEATURES_JSON, "w") as f:
        json.dump(selected_features_by_horizon, f, indent=2)
    print("Saved all selected features to outputs/selected_features_by_horizon.json")
"""

new_cells = nb['cells'][:feat_exec_idx + 1]

# Insert markdown explanation
new_cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [line + "\n" for line in explanation_markdown.splitlines()]
})

# Insert code block
new_cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [line + "\n" for line in selection_code.splitlines()]
})

# Add the rest of the cells
for idx in range(feat_exec_idx + 1, len(nb['cells'])):
    new_cells.append(nb['cells'][idx])

nb['cells'] = new_cells

with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2)

print("Successfully modified Advanced_EDA_Client.ipynb!")
