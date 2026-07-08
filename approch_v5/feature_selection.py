"""
Approach v5 - Feature Selection Module
Implements the 2-pass feature reduction pipeline:
Pass 1: SHAP TreeExplainer ranking
Pass 2: Lasso L1 / Recursive Feature Elimination (RFE)
Enforces a target of 12-15 features with justification logging.
"""

import os
import logging
import pandas as pd
import numpy as np
import lightgbm as lgb
import shap
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import RFE
from sklearn.ensemble import RandomForestRegressor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ApproachV5Selection")

def shap_first_pass_selection(X_train, y_train, threshold=1e-4):
    """
    Pass 1: SHAP Selection.
    Fits a baseline LightGBM model and extracts SHAP values to filter out low-impact features.
    
    Args:
        X_train (pd.DataFrame): Training features.
        y_train (pd.Series or np.array): Training targets.
        threshold (float): Minimum mean absolute SHAP value to keep.
        
    Returns:
        list: Filtered feature names.
    """
    logger.info("Executing Pass 1: SHAP TreeExplainer Feature Importance Filtering...")
    
    # Fit a fast LightGBM regressor
    model = lgb.LGBMRegressor(
        n_estimators=100,
        learning_rate=0.05,
        random_state=42,
        verbosity=-1,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # Compute SHAP values
    explainer = shap.TreeExplainer(model)
    # Using a subset of X_train (e.g. 5000 rows) to keep execution fast on CPU
    sample_size = min(5000, len(X_train))
    X_sample = X_train.sample(n=sample_size, random_state=42)
    shap_values = explainer.shap_values(X_sample)
    
    # Calculate mean absolute SHAP value per feature
    mean_shap = np.abs(shap_values).mean(axis=0)
    shap_df = pd.DataFrame({"Feature": X_train.columns, "Mean_Abs_SHAP": mean_shap})
    shap_df = shap_df.sort_values(by="Mean_Abs_SHAP", ascending=False)
    
    # Filter features based on threshold
    filtered_df = shap_df[shap_df["Mean_Abs_SHAP"] >= threshold]
    selected_features = filtered_df["Feature"].tolist()
    
    logger.info(f"SHAP Pass 1 completed. Kept {len(selected_features)} features (out of {len(X_train.columns)}) using threshold {threshold}.")
    return selected_features

def rfe_lasso_second_pass_selection(X_train, y_train, target_count=12):
    """
    Pass 2: Secondary Selection (Lasso or RFE).
    Compresses the feature set down to exactly 12-15 features.
    
    Args:
        X_train (pd.DataFrame): Training features (from Pass 1).
        y_train (pd.Series/np.array): Training targets.
        target_count (int): Targeted number of features (e.g. 12).
        
    Returns:
        list: Selected feature names (length <= 15).
    """
    logger.info(f"Executing Pass 2: LassoCV L1 Regularization selection (Target: {target_count} features)...")
    
    # Standardize data for Lasso convergence
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    # Fit LassoCV to automatically select alpha
    lasso = LassoCV(cv=5, random_state=42, max_iter=2000, n_jobs=-1)
    lasso.fit(X_train_scaled, y_train)
    
    # Extract coefficients
    coef_df = pd.DataFrame({"Feature": X_train.columns, "Coefficient": lasso.coef_})
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
        selector.fit(X_train, y_train)
        selected_features = X_train.columns[selector.support_].tolist()
        
    logger.info(f"Pass 2 selection completed. Final {len(selected_features)} features selected.")
    return selected_features

def justification_logging_framework(features, performance_metrics, baseline_threshold=0.80):
    """
    Monitors model validation performance on the selected 12-15 features.
    If the metric (e.g., F1-score) falls below the baseline_threshold,
    logs a detailed justification warning and triggers fallback logging.
    
    Args:
        features (list): Selected features list.
        performance_metrics (dict): Dict of current validation metrics (F1, Precision, etc.).
        baseline_threshold (float): Minimum acceptable F1-score threshold.
        
    Returns:
        bool: True if fallback is justified, False otherwise.
    """
    current_f1 = performance_metrics.get("f1", 0.0)
    if current_f1 < baseline_threshold:
        logger.warning(
            f"CRITICAL PERFORMANCE DEGRADATION: Feature count reduction to {len(features)} "
            f"degraded validation F1-score to {current_f1:.4f} (below threshold {baseline_threshold:.4f}).\n"
            f"Justification Statement:\n"
            f"  - The 12-15 feature boundary is omitting highly descriptive rolling standard deviations/differences.\n"
            f"  - Dynamic fallback triggered. Recommending expansion to 20 features for SME review."
        )
        return True
    logger.info(f"Performance check passed. F1-score: {current_f1:.4f} is above threshold.")
    return False
