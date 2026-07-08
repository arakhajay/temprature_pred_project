# Walkthrough - Approach v5 Validation Guide

This walkthrough provides step-by-step instructions for client engineers and reviewers to execute, evaluate, and validate the Approach v5 deliverables. 

Approach v5 establishes a high-performance temperature alert prediction framework using a highly compressed sensor configuration (**maximum of 12 features**), verified on PyTorch LSTM and Seq2Seq neural networks.

---

## 1. Directory Structure

All Approach v5 deliverables are contained within the `approch_v5/` folder:
* **Notebooks**: Walk through the research lifecycle cell-by-cell. Every notebook is fully self-contained, defining all functions, models, and loops directly inside its own cells for easy cell-by-cell client explanation.
* **Scripts**: Contain underlying helper classes, datasets, models, and training routines (used primarily by the Streamlit dashboard and compiler).
* **Documentation**: Outline files, explanatory documents, and compile scripts.
* **Streamlit Console**: Interactive dashboard showing predictions live on historian upset events.

---

## 2. Steps to Validate the Work

To validate the end-to-end V5 process, execute the notebooks and scripts in the following chronological order:

### Step 1: Data Profiling & Splits (EDA)
* **File**: [Detailed_EDA_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Detailed_EDA_v5.ipynb)
* **What to validate**: 
  - Verify that the raw DCS tags are reindexed to a 1-minute grid and short gaps (<= 5m) are forward-filled.
  - Review the chronological alarm-based splitting boundary timestamps. Confirm that Train (75%), Val (12.5%), and Test (12.5%) partitions correspond to active alarm frequencies.

### Step 2: Feature Engineering (Expansion)
* **File**: [Feature_Engineering_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Feature_Engineering_v5.ipynb)
* **What to validate**:
  - Review how the base variables are expanded into ~132 features (lags, rolling averages, differences/velocities, and thermodynamic interaction variables).

### Step 3: Two-Pass Feature Selection (Reduction)
* **File**: [Feature_Selection_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Feature_Selection_v5.ipynb)
* **What to validate**:
  - Run the selection cells. Pass 1 filters variables by global SHAP TreeExplainer values. Pass 2 runs Lasso (L1) regression to drive collinear weights to zero, yielding exactly **12 selected features**.
  - Review the logged output of the `justification_logging_framework`, which validates performance thresholds.

### Step 4: Model Training
* **File**: [Models_Training_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Models_Training_v5.ipynb)
* **What to validate**:
  - Review the training logs for the PyTorch LSTM and Seq2Seq Encoder-Decoder. Confirm validation loss tracks early stopping checkpoints and saves weights under `models/v5/`.

### Step 5: Metric Comparison & Scenario Visualizations
* **File**: [Model_Performance_Comparison_v5.ipynb](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/Model_Performance_Comparison_v5.ipynb)
* **What to validate**:
  - Review computed F1, Precision, Recall, and False Alarm Rates (FAR) on the test split.
  - Check the output plot of actual vs. predicted temperature trends during a holdout alarm episode.

### Step 6: Streamlit Interactive Dashboard
* **Command**: Run the following in your terminal from the project root:
  ```bash
  streamlit run approch_v5/app_v5.py
  ```
* **What to validate**:
  - Open the console in your browser (default: `http://localhost:8501`).
  - Toggle between the **Stable Operation** and **Critical Upset** scenarios in the sidebar.
  - Observe how the LSTM warns of crossings and the Seq2Seq projects the continuous 60-minute future heating slope on the interactive Plotly graph.
  - Verify that the 12 selected features are listed.

---

## 3. Explanations & Reports

* **Client Explanations File**: Read [explanation.md](file:///d:/Python-2025/Antigravity/honeywell/approch_v5/explanation.md) for a detailed technical discussion on splitting, collinearity handling, and dual-model control room deployment.
* **Final Compiled PDF Report**: View [Model_Performance_Report_v5.pdf](file:///d:/Python-2025/Antigravity/honeywell/docs/Model_Performance_Report_v5.pdf) for the publication-grade performance summary, featuring full-size tables, charts, and recommendations.
