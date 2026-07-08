# Presentation Deck Outline: Approach V5 Overview

This document outlines the slide structure and content cards for the Approach V5 stakeholder deck.

---

## Slide 1: Title Slide
* **Title:** Approach V5: Strict Feature Reduction & Deep Learning for Column Temperature Alerts
* **Subtitle:** Alarm-Based chronological Splitting and Two-Pass Sensor Selection (12–15 Features)
* **Metadata:** July 2026 | Process Safety & ML engineering Group

---

## Slide 2: Executive Context & Objectives
* **Core Problem:** Process alarm fatigue. Overhead temperatures must be predicted up to 60 minutes in advance.
* **Key Challenge:** Prior approaches used up to 132 features, making live deployment complex.
* **Objective:** Prove that a highly sparse feature set (maximum of 12–15 features) can predict alarms with comparable precision using LSTM and Seq2Seq networks.

---

## Slide 3: chronological Alarm-Based Splits
* **Visual:** Diagram of the timeline split based on alarm segment frequency.
* **Key Points:**
  - Standard time splits risk having sparse alarm density in testing or validation splits.
  - V5 splits partition the dataset timeline chronologically to achieve exactly a 75% / 12.5% / 12.5% distribution of distinct alarm sequences.
  - Zero leakage: no overlap across sequences.

---

## Slide 4: Feature Expansion Phase
* **Content:** Overview of the candidate feature pool.
* **Bullet Points:**
  - Base tag values, time context.
  - Lags (direction and velocity).
  - Rolling & Expanding statistics.
  - Cross-sensor interaction indicators.

---

## Slide 5: The Two-Pass Selection Pipeline
* **Visual:** Flowchart of features passing through the 2 filters.
* **Pass 1 (SHAP):** Filters out noise and weakly correlated variables.
* **Pass 2 (Lasso / RFE):** Eliminates collinearity and reduces feature dimension to 12–15.
* **Self-Check Logic:** Automatic justification logging if validation performance falls below F1 = 80%.

---

## Slide 6: Model Architectures: LSTM vs. Seq2Seq
* **LSTM:** Predicts temperature value at a specific future step. Optimized for low false alarms.
* **Seq2Seq:** Autoregressively generates the entire future 60-step curve. Optimized for predicting complete upset trajectories.

---

## Slide 7: Operations Visualization & Recommendations
* **Key Visual:** Mockup overlay showing a predicted temperature curve matching an actual alarm event.
* **Key Guidelines:**
  - Dashed projection curves on HMI screens to warn operators.
  - Dual-model alerting engine: high precision (LSTM) + high sensitivity (Seq2Seq).
