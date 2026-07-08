# Technical Report Outline: Approach V5 Methodology

## Document Metadata
* **Title:** Deep Learning Temperature Alarm Predictor (Approach V5)
* **Author:** Data Science & ML Engineering Team
* **Target Audience:** Process Control Engineers, Operations Safety SMEs
* **Version:** 5.0 (Strict Feature Selection & Alarm-Based Split)

---

## Section 1: Executive Summary & Project Goals
* **Problem Statement:** Reducing column overhead temperature alarms (threshold $\ge 21.0^\circ\text{C}$ for tag `03TIC_1023.PV`).
* **Approach V5 Objective:** Compress features strictly down to **12–15 features** using a robust 2-pass selection pipeline, and train LSTM/Seq2Seq architectures to verify if predictive accuracy is maintained with a highly sparse sensor set.

---

## Section 2: Exploratory Data Analysis & Preprocessing
* **Historical Baseline:** Data summary across Jan 2022 to Jan 2026.
* **Regularization Grid:** Reindexing to 1-minute intervals and handling of trips and plant shutdowns (handling gaps larger than 5 minutes as `NaN`).

---

## Section 3: Alarm-Based chronological Data Splitting
* **Methodology:** Chronological split boundaries designed to partition the dataset based on active alarm sequences:
  - 75% of alarms grouped into the **Training Split** (approx. 2022-2025).
  - 12.5% of alarms grouped into the **Validation Split** (mid 2025).
  - 12.5% of alarms grouped into the **Testing Split** (H2 2025 - Jan 2026).
* **Rationale:** Ensures representative validation/test metrics that are not skewed by dry periods without alarms, while strictly avoiding future data leakage.

---

## Section 4: High-Dimensional Feature Engineering (Expansion Phase)
* **Candidates Library:** Complete description of the candidates:
  - Rolling windows (mean, std, min, max).
  - Lags and rate of change.
  - Interaction ratios and time context variables.

---

## Section 5: Two-Pass Feature Selection (Target: 12–15 Features)
* **Pass 1: SHAP TreeExplainer Importance:**
  - Fitting an initial tree ensemble and calculating Shapley Additive Explanations.
  - Filtering out features with low global importance.
* **Pass 2: Lasso Regularization / Recursive Feature Elimination (RFE):**
  - Secondary reduction to select exactly 12–15 features.
* **Fallback & Justification Framework:**
  - Conditions under which feature count limits can be dynamically expanded (e.g., F1-score drop below 80%).

---

## Section 6: Deep Learning Architectures
* **LSTM Model:** Single-horizon prediction setup.
* **Seq2Seq Encoder-Decoder:** Multi-step continuous sequence output (forecast $t+1$ to $t+60$).

---

## Section 7: Comparative Performance Analysis
* **Evaluation Matrix:** Table template outlining comparison of V5 models against V4 (25 features) and V3 (132 features) baseline.
* **Metrics:** F1, Precision, Recall, False Alarm Rate, MAE, and RMSE.

---

## Section 8: Operations Deployment Recommendations
* **alerting configuration:** Integration into the Distributed Control System (DCS) historian.
* **Confidence Boundaries:** Visual forecasting trends for operators.
