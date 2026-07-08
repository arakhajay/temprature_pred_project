# Approach V5: Comprehensive Methodology & Client-Facing Explanation

This document serves as a detailed guide explaining the engineering and machine learning rationale behind Approach V5, covering the entire pipeline from Exploratory Data Analysis (EDA) to the live Streamlit dashboard.

---

## 1. Chronological Alarm-Based Data Splitting
### The Problem with Random Splits in Time-Series
In standard tabular machine learning, datasets are shuffled and split randomly (e.g. K-fold cross-validation). In time-series forecasting, this introduces **data leakage** because rolling statistics (means, standard deviations, differences) computed at time $t$ contain information from historical and future steps $t-1, \dots, t+60$. 

### The Problem with Standard Chronological Splits
A simple chronological split (e.g., splitting exactly at 75% of the timeline) runs the risk that alarm events are extremely sparse. If the last 25% of the timeline (the validation/test period) corresponds to a stable operational period with no plant upsets, we cannot compute reliable alarm performance metrics (Precision, Recall, FAR) because there are no actual alarms to evaluate.

### The V5 Alarm-Based Splitting Solution
* We identify all contiguous alarm blocks where the overhead cooling temperature is above the safety threshold ($\ge 21.0^\circ\text{C}$).
* We partition the chronological timeline at the boundaries of these alarm groups so that exactly **75% of the alarm sequences** fall into the **Training Split**, **12.5%** into **Validation**, and **12.5%** into **Testing**.
* This preserves the arrow of time (zero data leakage) while guaranteeing a statistically representative distribution of process upsets across splits.

---

## 2. Rationale Behind Feature Engineering
Distillation column upsets are governed by physical thermodynamics, which exhibit high inertia (slow heating/cooling lags). We expand 19 base sensor signals into 132 features to capture:
1. **Lags**: Captures immediate direction (e.g., is temperature rising or falling over the last 15–30 minutes).
2. **Rolling Statistics**: Computes moving averages, minimums, maximums, and standard deviations over 10m, 30m, and 60m windows. Rolling averages filter out transient sensor noise, while standard deviations act as precursors to instability.
3. **Rates of Change (Deltas)**: Mathematical derivatives representing the velocity of temperature/pressure spikes.
4. **Interaction Terms**: Ratios and products of complementary sensors (e.g. pressure multiplied by inlet temperature) representing physical energy balances in the column.
5. **Time Context**: ambient conditions (diurnal cycles and seasonal variations) affect cooling efficiency, captured by cyclical hour, day, and month features.

---

## 3. Two-Pass Feature Selection Pipeline
High dimensionality causes overfitting and increases real-time computing requirements. Moreover, process variables exhibit **high collinearity** (e.g. column inlet temperature is 98% correlated with overhead temperature). V5 addresses this with a strict 2-pass selection:

### **Pass 1: SHAP TreeExplainer Filtering**
* We train a baseline ensemble model on the validation split.
* We compute **Shapley Additive Explanations (SHAP)** values, which distribute the prediction impact fairly among features.
* Features with low global importance (mean absolute SHAP $< 10^{-4}$) are discarded.

### **Pass 2: Lasso L1 / Recursive Feature Elimination (RFE)**
* To shrink the remaining set down to exactly **12–15 features**, we run a Lasso Regressor (L1 regularization) or RFE.
* L1 regularization drives redundant collinear coefficients to exactly zero, isolating only the most independent, highly informative sensor signals.

### **Justification & Fallback Check**
If validation F1-score drops below **80%**, the logging framework flags a process warning. This provides a detailed report on performance degradation for operations engineers to review, allowing a fallback expansion up to 20 features if safety metrics are compromised.

---

## 4. Model Architectures & Deployment Strategy
We train two PyTorch deep learning models:
1. **LSTM Regressor**: Optimized for single-horizon forecasting (e.g. 5m, 15m, 30m, 60m). LSTM cells maintain hidden states that model thermodynamic accumulation.
2. **Seq2Seq Encoder-Decoder**: The encoder processes the historical 10-minute sequence, and the decoder autoregressively projects the complete future 60-minute curve.

### **Dual-Model Deployment Recommendation**
* Use the **LSTM** model as the primary trigger for the 5-minute Emergency Warning, leveraging its high precision to avoid nuisance alarm fatigue.
* Display the **Seq2Seq** continuous 60-minute forecast as a trend line on the operator's display. If the predicted trend shows a sustained crossing of the 21.0 °C threshold, trigger early warning actions.
