import os
import json
import joblib
import pandas as pd

# Load selected features
with open("outputs/selected_features_by_horizon.json", "r") as f:
    selected_features_by_horizon = json.load(f)

features_15m = selected_features_by_horizon['15m']
features_60m = selected_features_by_horizon['60m']

# Load tuned models
model_15m = joblib.load("models/tuned_new/lgb_model_15m.pkl")
model_60m = joblib.load("models/tuned_new/lgb_model_60m.pkl")

# Extract importances
imp_15m = pd.Series(model_15m.feature_importances_, index=features_15m).sort_values(ascending=False)
imp_60m = pd.Series(model_60m.feature_importances_, index=features_60m).sort_values(ascending=False)

# Create combined table for top 5 features
rows = []
for rank in range(1, 6):
    feat_15 = imp_15m.index[rank-1] if rank <= len(imp_15m) else ""
    val_15 = int(imp_15m.values[rank-1]) if rank <= len(imp_15m) else ""
    feat_60 = imp_60m.index[rank-1] if rank <= len(imp_60m) else ""
    val_60 = int(imp_60m.values[rank-1]) if rank <= len(imp_60m) else ""
    
    rows.append({
        'Rank': rank,
        'Feature (15 Min)': feat_15,
        'Importance (15m)': val_15,
        'Feature (60 Min)': feat_60,
        'Importance (60m)': val_60
    })

df_imp = pd.DataFrame(rows)
output_path = "outputs/eda_reports/tuned_feature_importance.csv"
df_imp.to_csv(output_path, index=False)
print(f"Extracted tuned feature importances and saved to {output_path}:")
print(df_imp)
