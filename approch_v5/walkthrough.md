# Walkthrough: Deliverables Packaging & Validation Guide

The Approach V5 deliverables have been fully updated, verified, and packaged into a single ZIP archive, **`approch_v5.zip`**, located at the project workspace root.

This archive contains all the files, notebooks, scripts, models, subdirectories, and documentation for Approach V5 exactly as they are.

## ZIP Archive Contents
The ZIP file contains the `approch_v5/` directory which has:
* **All Jupyter Notebooks (`Detailed_EDA_v5.ipynb`, `Feature_Engineering_v5.ipynb`, `Feature_Selection_v5.ipynb`, `Models_Training_v5.ipynb`, `Model_Performance_Comparison_v5.ipynb`)** fully executed on the real dataset with cell outputs saved in-place.
* **All Python scripts (`initialize_model_pipeline.py`, `utils.py`, `models.py`, `train.py`, `evaluate.py`, `feature_selection.py`, `app_v5.py`, `generate_model_report_v5.py`)** used for the pipeline, report generation, and the dashboard.
* **Trained Weights (`models/v5/`)** for the LSTM and Seq2Seq networks and standard scalers.
* **Output Plots and Metrics (`outputs/v5/`)** containing scenario forecasts and comparison files.
* **`Model_Performance_Report_v5.pdf`**: The publication-grade, 9-page operations PDF report with newly-added KDE plots and F1-score comparisons.
* **`walkthrough.md`**: The client-facing guide at the unzipped root containing instructions for environment setup, notebook execution, and dashboard launching.
* **`explanation.md`**: The document describing splits, collinearity mitigation, and model rationales.

---

## Technical Features Implemented (Approach V5 Feedback)

### 1. Three-Phase Feature Selection Pipeline (`feature_selection.py`)
* **Phase 1: Initial Feature Selection**: Distance correlation analysis against the target and pairwise between all features. Top 5 dominant independent features are selected and set aside.
* **Phase 2: SHAP Feature Selection**: LightGBM regressor trained *only* on the remaining less dominant features. Top SHAP features are selected.
* **Phase 3: Lasso L1 Regularization**: A Lasso model is trained on the combined pool (dominant + SHAP selected) to further reduce the features down to exactly 12 final features.

### 2. Comprehensive Performance Plots & Visualizations
The notebooks and report now generate and display:
1. **Distance Correlation Rankings** (`distance_correlation_rankings.png`)
2. **SHAP Feature Importance** (`shap_feature_importance.png`)
3. **Lasso Coefficients** (`lasso_coefficients.png`)
4. **Epoch Plots** (Training vs. Validation loss for both LSTM and Seq2Seq: `lstm_epoch_loss.png`, `seq2seq_epoch_loss.png`)
5. **KDE Plot** (Actual vs. Predicted temperature distributions with Train, Validation, and Test datasets overlaid: `actual_vs_predicted_kde.png`)
6. **Time-Series Plot** (Actual vs. Predicted temperature during a test alert episode: `lstm_alert_episode.png`)
7. **Model Performance Comparison** (Comparative F1-score chart across warning horizons: `f1_score_comparison.png`)

---

## Validation Steps for the Client

### 1. Extract the Archive
Unzip the file `approch_v5.zip` on your local system.

### 2. Set Up the Environment
Create a virtual environment running Python 3.10+ and install the dependencies:
```bash
pip install pandas numpy torch lightgbm shap scikit-learn matplotlib seaborn streamlit plotly pyarrow reportlab pillow
```

### 3. Run the Notebooks (Cell-by-Cell)
Open the unzipped directory and run the notebooks in order (or run `python approch_v5/run_all_notebooks.py` to run all in-place):
1. **[Detailed_EDA_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Detailed_EDA_v5.ipynb)** (exploratory data analysis, MICE imputation, and alarm splitting).
2. **[Feature_Engineering_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Feature_Engineering_v5.ipynb)** (generating lags, averages, rate-of-change, and interaction tags).
3. **[Feature_Selection_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Feature_Selection_v5.ipynb)** (Three-phase selection using distance correlation, SHAP, and Lasso L1 regularization).
4. **[Models_Training_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Models_Training_v5.ipynb)** (PyTorch LSTM and Seq2Seq training loops, outputting epoch plots).
5. **[Model_Performance_Comparison_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Model_Performance_Comparison_v5.ipynb)** (evaluation scoring, actual vs. predicted KDE overlay, and warning horizon plots).

### 4. Run the Streamlit Dashboard
To run the interactive simulated control room dashboard:
```bash
streamlit run app_v5.py
```
This will start the dev server and open `http://localhost:8501` in your default browser. Toggle between **Stable Operation** and **Critical Upset** scenarios in the sidebar to visualize the predictive performance.
