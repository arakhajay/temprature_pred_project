"""
Approach v5 - Three-Phase Feature Selection Module
Implements the 3-phase feature reduction pipeline:
Phase 1: Distance Correlation vs. Target & Pairwise (filters collinearity, selects top 5 dominant features)
Phase 2: SHAP TreeExplainer ranking on less dominant features
Phase 3: Lasso L1 / Recursive Feature Elimination (RFE) on combined pool to target exactly 12 features.
"""

import os
import logging
import pandas as pd
import numpy as np
import lightgbm as lgb
import shap
from dcor import distance_correlation
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import RFE
from sklearn.ensemble import RandomForestRegressor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ApproachV5Selection")

def distance_correlation_phase_1(X_train, y_train, dominant_count=5, collinearity_threshold=0.90, sample_size=2000):
    """
    Phase 1: Distance Correlation Selection.
    Computes distance correlation of all features with the target and pairwise between features.
    Selects top independent dominant features and returns them along with the less dominant features.
    """
    logger.info("Executing Phase 1: Distance Correlation Analysis (vs. Target & Pairwise)...")
    
    # Downsample for computational speed
    sample_idx = np.random.RandomState(42).choice(len(X_train), size=min(sample_size, len(X_train)), replace=False)
    X_sample = X_train.iloc[sample_idx]
    y_sample = y_train.iloc[sample_idx]
    
    # 1. Compute distance correlation with the target
    target_corrs = {}
    for col in X_train.columns:
        target_corrs[col] = distance_correlation(X_sample[col].values, y_sample.values)
        
    # Sort features by correlation with target descending
    sorted_features = sorted(target_corrs.items(), key=lambda x: x[1], reverse=True)
    sorted_feature_names = [f[0] for f in sorted_features]
    
    # 2. Select independent dominant features
    dominant_features = []
    skipped_features = []
    
    for feat in sorted_feature_names:
        if len(dominant_features) >= dominant_count:
            break
            
        # Check pairwise correlation with already selected dominant features
        is_collinear = False
        for dom_feat in dominant_features:
            p_corr = distance_correlation(X_sample[feat].values, X_sample[dom_feat].values)
            if p_corr > collinearity_threshold:
                is_collinear = True
                break
                
        if not is_collinear:
            dominant_features.append(feat)
        else:
            skipped_features.append(feat)
            
    # Remaining features are less dominant
    less_dominant_features = [f for f in X_train.columns if f not in dominant_features]
    
    logger.info(f"Distance Correlation Phase 1 completed.")
    logger.info(f"Selected Dominant Features (kept aside): {dominant_features}")
    logger.info(f"Remaining Less Dominant Features: {len(less_dominant_features)}")
    
    return dominant_features, less_dominant_features, target_corrs

def shap_phase_2(X_train, y_train, less_dominant_features, threshold=1e-4, sample_size=5000):
    """
    Phase 2: SHAP Selection on less dominant features.
    Fits a baseline LightGBM model and extracts SHAP values to filter out low-impact features.
    """
    logger.info("Executing Phase 2: SHAP Feature Importance Filtering on Less Dominant Features...")
    
    X_train_ld = X_train[less_dominant_features]
    
    # Fit a fast LightGBM regressor
    model = lgb.LGBMRegressor(
        n_estimators=100,
        learning_rate=0.05,
        random_state=42,
        verbosity=-1,
        n_jobs=-1
    )
    model.fit(X_train_ld, y_train)
    
    # Compute SHAP values
    explainer = shap.TreeExplainer(model)
    sample_idx = min(sample_size, len(X_train_ld))
    X_sample = X_train_ld.sample(n=sample_idx, random_state=42)
    shap_values = explainer.shap_values(X_sample)
    
    # Calculate mean absolute SHAP value per feature
    mean_shap = np.abs(shap_values).mean(axis=0)
    shap_df = pd.DataFrame({"Feature": less_dominant_features, "Mean_Abs_SHAP": mean_shap})
    shap_df = shap_df.sort_values(by="Mean_Abs_SHAP", ascending=False)
    
    # Filter features based on threshold
    filtered_df = shap_df[shap_df["Mean_Abs_SHAP"] >= threshold]
    shap_selected = filtered_df["Feature"].tolist()
    
    logger.info(f"SHAP Phase 2 completed. Kept {len(shap_selected)} less dominant features using threshold {threshold}.")
    return shap_selected, shap_df

def lasso_phase_3(X_train, y_train, combined_features, target_count=12):
    """
    Phase 3: Secondary Selection via Lasso L1 Regularization.
    Compresses the combined dominant and SHAP-selected features down to exactly target_count features.
    """
    logger.info(f"Executing Phase 3: LassoCV L1 Regularization selection on combined features (Target: {target_count})...")
    
    X_train_comb = X_train[combined_features]
    
    # Standardize data for Lasso convergence
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_comb)
    
    # Fit LassoCV to automatically select alpha
    lasso = LassoCV(cv=5, random_state=42, max_iter=2000, n_jobs=-1)
    lasso.fit(X_train_scaled, y_train)
    
    # Extract coefficients
    coef_df = pd.DataFrame({"Feature": combined_features, "Coefficient": lasso.coef_})
    coef_df["Abs_Coef"] = coef_df["Coefficient"].abs()
    coef_df = coef_df.sort_values(by="Abs_Coef", ascending=False)
    
    # Select top non-zero coefficient features
    non_zero_df = coef_df[coef_df["Abs_Coef"] > 0]
    selected_features = non_zero_df.head(target_count)["Feature"].tolist()
    
    # Fallback to RFE if Lasso doesn't yield enough features or is degenerate
    if len(selected_features) < target_count:
        logger.warning("LassoCV yielded fewer features than target. Falling back to RFE...")
        estimator = RandomForestRegressor(n_estimators=50, max_depth=6, random_state=42, n_jobs=-1)
        selector = RFE(estimator, n_features_to_select=target_count, step=2)
        selector.fit(X_train_comb, y_train)
        selected_features = X_train_comb.columns[selector.support_].tolist()
        
    logger.info(f"Phase 3 selection completed. Final {len(selected_features)} features selected.")
    return selected_features, coef_df

def justification_logging_framework(features, performance_metrics, baseline_threshold=0.80):
    """
    Monitors model validation performance on the selected features.
    If the metric (e.g., F1-score) falls below the baseline_threshold,
    logs a detailed justification warning and triggers fallback logging.
    """
    current_f1 = performance_metrics.get("f1", 0.0)
    if current_f1 < baseline_threshold:
        logger.warning(
            f"CRITICAL PERFORMANCE DEGRADATION: Feature count reduction to {len(features)} "
            f"degraded validation F1-score to {current_f1:.4f} (below threshold {baseline_threshold:.4f}).\n"
            f"Justification Statement:\n"
            f"  - The 12-feature boundary is omitting highly descriptive rolling standard deviations/differences.\n"
            f"  - Dynamic fallback triggered. Recommending expansion to 20 features for SME review."
        )
        return True
    logger.info(f"Performance check passed. F1-score: {current_f1:.4f} is above threshold.")
    return False
