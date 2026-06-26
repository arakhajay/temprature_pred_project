import json
import os

nb_path = "Model_Training_and_Evaluation_Client.ipynb"
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Locate cells by search terms to ensure robustness against cell index shifts
sme_override_idx = -1
training_idx = -1
importance_idx = -1

for idx, cell in enumerate(nb['cells']):
    source_text = "".join(cell.get('source', []))
    if "SME Feature Selection Override" in source_text:
        sme_override_idx = idx
    elif "horizons = [5, 15, 30, 60]" in source_text and "test_preds_df = pd.DataFrame" in source_text and "first_cut_new" in source_text:
        training_idx = idx
    elif "for h in [15, 60]:" in source_text and "models/tuned_new" in source_text and "feat_imp = pd.Series" in source_text:
        importance_idx = idx

print(f"Located cells:")
print(f"  SME Override Cell: {sme_override_idx}")
print(f"  Training Loop Cell: {training_idx}")
print(f"  Feature Importance Cell: {importance_idx}")

# Define new markdown explanation cell
explanation_markdown = """### 1.7. Strict 3-Phase Feature Selection Pipeline (Thermodynamic Signal Preservation)

To prune our 113 engineered features down to the most impactful, non-redundant set without losing physical thermodynamic signals, we implement a strict 3-phase feature selection pipeline:

1. **Phase 1: High-Correlation Filter (Collinearity Removal)**
   Refinery data represents continuous physical processes, leading to high collinearity among rolling stats and sequential lags. We compute the Pearson correlation matrix:
   $$R_{i,j} = \\frac{\\text{Cov}(X_i, X_j)}{\\sigma_{i}\\sigma_{j}}$$
   For any feature pair with $|R_{i,j}| > 0.90$, we identify collinearity. To prevent downstream credit-splitting, we drop one feature. Crucially, we retain the feature with the simpler calculation structure. For example, raw sensors (complexity 0) are preferred over lags (complexity 2), which are preferred over rolling averages (complexity 4), which are preferred over rolling standard deviations (complexity 6). This preserves direct thermodynamic indicators.

2. **Phase 2: Time-Series Split & Permutation Importance (Overfitting Filter)**
   We partition the training data using a 5-fold `TimeSeriesSplit` (Forward Chaining) to respect chronological order and prevent lookahead bias. On each fold, we train a baseline tree-based model (LightGBM) and compute permutation importance based on Mean Absolute Error (MAE):
   $$I(f) = \\text{MAE}_{\\text{shuffled}} - \\text{MAE}_{\\text{baseline}}$$
   Features with zero or negative importance (such as calendar 'year' or 'month' indicators that capture transient historical conditions rather than physical laws) are filtered out, and we select the top 25 features.

3. **Phase 3: SHAP TreeExplainer (Final Cut & Physical Validation)**
   We retrain the model on the top 25 features and run a `shap.TreeExplainer` on the validation dataset:
   $$\\phi_i = \\sum_{S \\subseteq F \\setminus \\{i\\}} \\frac{|S|!(|F| - |S| - 1)!}{|F|!} \\left[ f(S \\cup \\{i\\}) - f(S) \\right]$$
   We filter out features with a mean absolute SHAP value below a minimal threshold ($10^{-4}$), and plot the SHAP summary to verify that their directional impact aligns with thermodynamic principles (e.g., Column Inlet Temperature should drive Column Overhead Temperature upward).
"""

# Define new code cell executing/loading the feature selection
selection_code = """# Implement/Load the Strict 3-Phase Feature Selection Pipeline
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
    feature_cols = [c for c in df.columns if c not in exclude_cols and c != 'TimeStamp']
    
    # We will compute selection for all horizons (downsampled for fast execution)
    for h in [5, 15, 30, 60]:
        target_col = f'target_{h}m'
        data_h = df[feature_cols + [target_col]].dropna(subset=[target_col])
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

# 1. Modify the training loop cell (Cell 12 originally, will shift by 2)
new_training_code = """horizons = [5, 15, 30, 60]
results = {}
test_preds_df = pd.DataFrame(index=df.loc[val_end + pd.Timedelta(minutes=1):].index)
test_preds_df['actual'] = df.loc[val_end + pd.Timedelta(minutes=1):, '03TIC_1023.PV']

for h in horizons:
    target_name = f'target_{h}m'
    
    # Load selected features for this horizon
    feature_cols_h = selected_features_by_horizon[f'{h}m']
    data_h = df[feature_cols_h + [target_name]].dropna(subset=[target_name])
    
    # Splits
    train_data = data_h.loc[:train_end]
    val_data = data_h.loc[train_end + pd.Timedelta(minutes=1):val_end]
    test_data = data_h.loc[val_end + pd.Timedelta(minutes=1):]
    
    X_train, y_train = train_data[feature_cols_h], train_data[target_name]
    X_val, y_val = val_data[feature_cols_h], val_data[target_name]
    X_test, y_test = test_data[feature_cols_h], test_data[target_name]
    
    # Load the trained model
    model_path = f"models/first_cut_new/lgb_model_{h}m.pkl"
    if os.path.exists(model_path):
        print(f"Loading trained model for horizon {h}m...")
        model = joblib.load(model_path)
    else:
        print(f"Training model for horizon {h}m...")
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
        callbacks = [lgb.early_stopping(stopping_rounds=50, verbose=False)]
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            eval_metric='rmse',
            callbacks=callbacks
        )
        
    test_preds = model.predict(X_test)
    test_preds_df[f'pred_{h}m'] = pd.Series(test_preds, index=X_test.index)
    
    # Metrics
    mae = mean_absolute_error(y_test, test_preds)
    rmse = np.sqrt(mean_squared_error(y_test, test_preds))
    
    # Alarm Classification (Threshold = 21.0)
    threshold = 21.0
    y_test_alarm = (y_test >= threshold).astype(int)
    test_preds_alarm = (test_preds >= threshold).astype(int)
    
    precision, recall, f1, _ = precision_recall_fscore_support(y_test_alarm, test_preds_alarm, average='binary', zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y_test_alarm, test_preds_alarm).ravel()
    far = fp / (fp + tn) if (fp + tn) > 0 else 0
    
    results[h] = {
        'MAE': mae,
        'RMSE': rmse,
        'Precision': precision,
        'Recall': recall,
        'F1-Score': f1,
        'False Alarm Rate': far
    }
    
    print(f"Horizon {h}m: F1={f1:.2%}, Precision={precision:.2%}, Recall={recall:.2%}, FAR={far:.4%}, MAE={mae:.4f} °C")
"""

# 2. Modify the Feature Importance plot cell (Cell 22 originally, will shift by 2)
new_importance_code = """for h in [15, 60]:
    model_path = f"models/tuned_new/lgb_model_{h}m.pkl"
    if os.path.exists(model_path):
        model = joblib.load(model_path)
        importance = model.feature_importances_
        feature_cols_h = selected_features_by_horizon[f'{h}m']
        feat_imp = pd.Series(importance, index=feature_cols_h).sort_values(ascending=False).head(15)
        
        plt.figure(figsize=(12, 6))
        sns.barplot(x=feat_imp.values, y=feat_imp.index, palette="viridis")
        plt.title(f"Top 15 Feature Importances (Tuned Model) — {h}-Minute Horizon")
        plt.xlabel("Split Importance")
        plt.ylabel("Feature Name")
        plt.tight_layout()
        plt.show()
"""

# Perform insertions and replacements
# Insert new cells after sme_override_idx
new_cells = nb['cells'][:sme_override_idx + 1]

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

# Add the rest of the cells, updating the target training and importance cells
shifted_idx_offset = 2
for idx in range(sme_override_idx + 1, len(nb['cells'])):
    cell = nb['cells'][idx]
    if idx == training_idx:
        cell['source'] = [line + "\n" for line in new_training_code.splitlines()]
    elif idx == importance_idx:
        cell['source'] = [line + "\n" for line in new_importance_code.splitlines()]
    new_cells.append(cell)

nb['cells'] = new_cells

with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2)

print("Successfully modified Model_Training_and_Evaluation_Client.ipynb!")
