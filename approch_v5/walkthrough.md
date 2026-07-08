# Walkthrough: Approach V5 Deliverables Guide

Welcome to the **Approach V5 Temperature Alarm Forecasting** project package. This guide provides step-by-step instructions for process safety, operations, and control room engineers to set up the environment, run the Jupyter Notebooks, and launch the interactive Streamlit dashboard.

---

## 1. Directory Structure

This archive contains the complete Approach V5 workspace as-is:
* **Jupyter Notebooks (`.ipynb`)**:
  * [Detailed_EDA_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Detailed_EDA_v5.ipynb) - Exploratory Data Analysis, imputation, gap profiling, and alarm splits.
  * [Feature_Engineering_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Feature_Engineering_v5.ipynb) - Lag variables, rolling windows, rates of change, and thermodynamically-engineered interaction terms.
  * [Feature_Selection_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Feature_Selection_v5.ipynb) - Two-pass selection (SHAP TreeExplainer and Lasso L1 regularization) reducing features to exactly 12.
  * [Models_Training_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Models_Training_v5.ipynb) - Self-contained PyTorch training cells for both LSTM and Seq2Seq networks.
  * [Model_Performance_Comparison_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Model_Performance_Comparison_v5.ipynb) - Test evaluation, metric summary CSV writing, and F1 bar plotting.
* **Modular Python Scripts (`.py`)**:
  * `initialize_model_pipeline.py` - Sets up baseline models, scaling profiles, and comparison baselines.
  * `utils.py` - Reusable data processing, loading, dataset preparation, and feature expansion logic.
  * `models.py` - Core network architectures (`LSTMRegressor`, `Seq2Seq`) in PyTorch.
  * `train.py` & `evaluate.py` - Helper scripts for console metric evaluations and actual-vs-predicted plotting.
  * `app_v5.py` - Streamlit console code.
  * `generate_model_report_v5.py` - PDF generation script.
* **Documentation (`.md` and `.pdf`)**:
  * [Model_Performance_Report_v5.pdf](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Model_Performance_Report_v5.pdf) - Publication-grade, 9-page executive operations report containing all project plots.
  * [explanation.md](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/explanation.md) - Physical, thermodynamic, and mathematical details of the V5 approach.
* **Subdirectories**:
  * `models/` - Saves scaling files and PyTorch trained weight matrices (`.pth`).
  * `outputs/` - Saves generated CSV metrics and PNG plots.
  * `docs/` - Original workspace documentation.

---

## 2. Environment Setup

To run the notebooks and Streamlit app, we recommend setting up a virtual environment running Python 3.10 or 3.11:

### Using pip
Open a shell at the unzipped project root and run:
```bash
pip install pandas numpy torch lightgbm shap scikit-learn matplotlib seaborn streamlit plotly pyarrow reportlab pillow
```

### Using conda
```bash
conda create -n honeywell_v5 python=3.10
conda activate honeywell_v5
conda install -c conda-forge pandas numpy pytorch lightgbm shap scikit-learn matplotlib seaborn streamlit plotly pyarrow reportlab pillow
```

---

## 3. How to Validate the Process (Notebooks)

Open your Jupyter client (`jupyter notebook` or VS Code) and run the five notebooks in chronological order:

1. **Step 1: Data Profiling & Splits** -> Open and run [Detailed_EDA_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Detailed_EDA_v5.ipynb)
   * *Validation*: Review the gap profiling plots and chronological alarm splits boundaries (75% Train / 12.5% Val / 12.5% Test). All figures are saved directly in the folder.
2. **Step 2: Feature Engineering** -> Open and run [Feature_Engineering_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Feature_Engineering_v5.ipynb)
   * *Validation*: Review how the base DCS tags are expanded into the 132-dimension candidate feature pool.
3. **Step 3: Two-Pass Selection** -> Open and run [Feature_Selection_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Feature_Selection_v5.ipynb)
   * *Validation*: Review the computed SHAP values plot (`shap_feature_importance.png`) and the Lasso coefficients plot (`lasso_coefficients.png`), shrinking the features to exactly 12.
4. **Step 4: Model Training** -> Open and run [Models_Training_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Models_Training_v5.ipynb)
   * *Validation*: Observe PyTorch training progress, loss convergence, and early stopping triggers.
5. **Step 5: Metric Evaluation** -> Open and run [Model_Performance_Comparison_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Model_Performance_Comparison_v5.ipynb)
   * *Validation*: Verify that the out-of-sample metrics are computed, saved to `outputs/v5/approach_v5_comparison.csv`, and plotted as a comparative F1-score chart (`f1_score_comparison.png`).

---

## 4. How to Launch the Streamlit Dashboard

To validate the models interactively in a simulated control room console:

1. Open your terminal at the unzipped project folder.
2. Run the following command:
   ```bash
   streamlit run app_v5.py
   ```
3. Your browser will automatically open to `http://localhost:8501`.
4. In the left-hand sidebar, toggle between **Stable Operation** and **Critical Upset** scenarios.
5. Review the live interactive Plotly charts illustrating the LSTM threshold warnings and the Seq2Seq continuous 60-minute future heating projections.
