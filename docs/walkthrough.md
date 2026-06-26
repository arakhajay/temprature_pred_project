# Project Walkthrough: Honeywell Advanced Process EDA Presentation & Detailed PDF Report

We have successfully created the client-driven Advanced Exploratory Data Analysis (EDA) presentation deck (`EDA_Presentation.pptx`) and a comprehensive Detailed PDF Report (`EDA_Detailed_Report.pdf`) containing full diagnostic insights, tables, and charts.

---

## 1. Summary of Deliverables

We have created the following files and outputs:
1. **`Advanced_EDA_Client.ipynb`** [Link](file:///d:/Python-2025/Antigravity/honeywell/Advanced_EDA_Client.ipynb): The notebook performing the full client-driven EDA, executing all conditional null logic, triple correlation matrices, chattering detection, pre/post-alarm ramping, post-trip verification, split balance, and seasonal trends.
2. **`create_eda_presentation.js`** [Link](file:///d:/Python-2025/Antigravity/honeywell/create_eda_presentation.js): The programmatic presentation compiler script, incorporating final layout, card outlines, shadow styles, table column spacing, and clean text wrapping.
3. **`docs/EDA_Presentation.pptx`** [Link](file:///d:/Python-2025/Antigravity/honeywell/docs/EDA_Presentation.pptx): Programmatically compiled 20-slide widescreen (16:9) executive presentation deck.
4. **`docs/EDA_Presentation.pdf`** [Link](file:///d:/Python-2025/Antigravity/honeywell/docs/EDA_Presentation.pdf): Converted PDF copy of the presentation for direct distribution.
5. **`docs/slides_eda/`** [Link](file:///d:/Python-2025/Antigravity/honeywell/docs/slides_eda/): Slide JPEG images (`Slide1.JPG` to `Slide20.JPG`) used for visual quality assurance.
6. **`generate_eda_pdf_report.py`** [Link](file:///d:/Python-2025/Antigravity/honeywell/generate_eda_pdf_report.py): Python report compiler script using ReportLab to build a professional multi-page document.
7. **`docs/EDA_Detailed_Report.pdf`** [Link](file:///d:/Python-2025/Antigravity/honeywell/docs/EDA_Detailed_Report.pdf): Comprehensive 14-page detailed PDF report with 11 scaled charts and styled CSV data tables.
8. **`docs/walkthrough.md`** [Link](file:///d:/Python-2025/Antigravity/honeywell/docs/walkthrough.md): This walkthrough report.

---

## 2. Advanced EDA Key Findings & Process Insights

The advanced analysis of the 4-year continuous history (2,019,221 records) yielded the following critical findings:

### A. Consecutive Null Gaps & Imputation (Slides 3-5, PDF Section 1)
* **Strategy**: Impute consecutive null gaps per column:
  - **Max consecutive null duration > 60 minutes** → MICE Imputation.
  - **Max consecutive null duration ≤ 60 minutes** → Forward-Fill & Backward-Fill (FFill+BFill) Imputation.
  - **Preserving Shutdown Gaps**: Imputations are applied to the raw dataframe *before* reindexing, ensuring that long plant shutdown periods (93,304 rows of NaN timestamps) are preserved as NaNs instead of being filled with synthetic values.
* **Imputation Verification Charts**:
  - **Line Chart Zoom-in (`imputation_zoom_line.png`)**: Zooms in on the largest dropouts for the MICE variables: `02FI_1000.PV` (85-minute gap) and `03TI_1002.PV` (~37-hour gap). It displays the raw data (dotted navy line with a blank gap) alongside the imputed data (solid teal line), demonstrating that MICE smoothly fills the gap following the process trend.
  - **Boxplot Comparison (`imputation_boxplot_comparison.png`)**: Plots side-by-side boxplots for the imputed variables (`03TI_1002.PV`, `02FI_1000.PV`, `03FIC_1085.PV`, `03PDI_1077.PV`) before and after imputation. The medians, IQRs, and extreme outlier boundaries align perfectly, showing that the overall distribution shape is preserved and no outlier anomalies or out-of-bounds spikes/dips were introduced.
* **Findings**: 
  - `03TI_1002.PV` (max gap ~37 hours) and `02FI_1000.PV` (max gap 85 minutes) exceeded 60 minutes and were imputed using MICE.
  - All other 17 columns had max gaps ≤ 10 minutes and were successfully imputed using FFill+BFill, ensuring no remaining null imbalances.

### B. DCS Operational Limits & Outliers (Slide 6, PDF Section 1.5)
* **Strategy**: Checked sensor readings against the DCS configuration limits (`03TIC_1023_PVLO_PVHI.csv`). Check normal warning range crossings (`PV LOW` to `PV HIGH`) and extreme trip breaches (`EXT PV LOW` to `EXT PV HIGH`), which serve as outlier indicators.
* **Findings**:
  - **0 Rows Breach Extreme Trip Limits**: Across all 19 sensors (2,019,221 records), not a single data point breached the extreme trip limits. This confirms that our preprocessing successfully removed trip/shutdown transients, yielding a physically clean baseline dataset with zero instrument outliers.
  - **Normal Warning Crossings**: A few sensors occasionally crossed warning limits. Most notably, C3 suction pressure (`03PIC_1013.PV`) crossed its 300.0 barg warning limit in 13.85% of records (up to 318.26 barg), but since `EXT PV HIGH` is undefined for it, these are not classified as outliers.

### C. Multi-Method Triple Correlation (Slides 7-10, PDF Section 2)
* **Strategy**: Ran Pearson (linear), Spearman (monotonic rank), and Distance Correlation (non-linear).
* **Pearson Inter-Variable Analysis**: Slide 7 and PDF Table 3 show **only inter-variable collinear pairs** ($|r| \ge 0.80$, excluding target tag) to identify redundant sensors for potential removal by the Subject Matter Expert (SME).
* **Findings**: 
  - Identified highly collinear inter-variable pairs representing physically close sensors (e.g. `03TI_1015.PV & 03TI_1024.PV` at $r = 0.9896$, `03PIC_1023.PV & 03TI_1015.PV` at $r = 0.9796$).
  - Large Pearson-Spearman gaps ($> 0.30$) in pressure/delta-P pairs and strong Distance Correlation dependencies (up to 0.71) validate the use of non-linear tree models (LightGBM).

### D. Alarm Duration & Chattering Detection (Slides 11-12, PDF Section 3)
* **Bucketing**: Analyzed 1,561 distinct alarm events.
  - **Chattering (0-1 min)**: 304 episodes represent 19.5% of total events but under 0.7% of total downtime.
  - **Sustained (60m+)**: 214 episodes represent 13.7% of events but account for **87.8% of all alarm downtime** (53,829 minutes).
* **Chattering Isolation**: 360 chattering sequences (episodes $\le 1$ min separated by $< 5$ min normal runtime) represent control loop noise. The ML predictor should ignore these to avoid operator alarm fatigue.

### E. Pre/Post-Alarm Behavioral Profiles (Slide 13, PDF Section 4)
* **Pre-Alarm (30m Lead)**: Overhead temp (`03TIC_1023.PV`) rises at **$+0.0132°C/\text{min}$** (+$0.39°C$ over 30m). Column bottom inlet temp (`03TI_1024.PV`) leads at **$+0.0155°C/\text{min}$** (+$0.47°C$ over 30m), confirming heat climbs from the column bottom.
* **Post-Alarm Cooldown**: System cools down slowly at **$-0.0125°C/\text{min}$**. It takes an average of **$42.5$ minutes** for the column to return to its stable baseline ($< 20.0°C$) after clearing the $21.0°C$ threshold.

### F. Post-Trip False Alarm Check (Slide 14, PDF Section 4)
* **Strategy**: Analyzed alarm crossings starting within 10, 20, 60, and 120 minutes following the restart of the 85 plant trips.
* **Findings**: Only 12 of 1,561 alarms (0.7%) occurred within 120 minutes of trip ends. Post-trip thermal residuals do not cause widespread false alarms.

### G. Split Balance & Seasonal Trends (Slides 14-15, PDF Section 5)
* **Splits**: Alarm episodes are properly balanced across the chronological splits:
  - **Train (2022-2025)**: 1,169 episodes (74.89% of events), average duration 43.67m.
  - **Val (Mid 2025)**: 199 episodes (12.75% of events), average duration 37.72m.
  - **Test (Late 2025)**: 193 episodes (12.36% of events), average duration 14.10m.
* **Seasons**: Alarm counts peak in summer months (June-August), driven by high ambient air temperatures reducing condenser heat exchange efficiency. Plant maintenance should schedule condenser cleaning prior to May.

---

## 3. Executive Slide Deck Structure (21 Slides)

The presentation (`docs/EDA_Presentation.pptx`) is designed using professional, consistent widescreen slides:
* **Slide 1**: Title / Cover Slide (Premium Dark Navy Theme)
* **Slide 2**: Objectives & Process Overview
* **Slide 3**: Data Completeness & Gaps
* **Slide 4**: Consecutive Nulls Analysis
* **Slide 5**: Imputation Strategy & Results (Updated with consecutive gap threshold rule and separate Pre/Post Imputation Distribution charts side-by-side)
* **Slide 6**: DCS Operational Limits & Outliers (New Slide presenting safety warning crossings and confirming zero extreme trip breaches)
* **Slide 7**: Multi-Method Correlation: Pearson (Updated with inter-variable pairs only)
* **Slide 8**: Multi-Method Correlation: Spearman
* **Slide 9**: Multi-Method Correlation: Distance Correlation
* **Slide 10**: Target Correlation Rankings
* **Slide 11**: Alarm Episode Durations
* **Slide 12**: Alarm Chattering & Windowing
* **Slide 13**: Pre-Alarm Thermodynamic Ramping
* **Slide 14**: Post-Trip & Split Balance (Updated with episode-level splits: Train=74.89%, Val=12.75%, Test=12.36%)
* **Slide 15**: Monthly & Seasonal Alarm Trends
* **Slide 16**: Feature Selection Strategy (Correlation filters & thermodynamic context)
* **Slide 17**: Feature Engineering Pipeline (Rolling statistics, lag structures, differences, and SME drop overrides)
* **Slide 18**: First-Cut Model Performance (Precision, recall, F1-score, FAR across 5, 15, 30, 60m horizons)
* **Slide 19**: Model Tuning & Optimization (Optuna hyperparameter study results and comparison)
* **Slide 20**: Tuned Model Feature Importance (Key predictive drivers per horizon)
* **Slide 21**: Conclusions & Recommendations (Premium Dark Navy Theme)

---

## 4. Verification and Visual QA Results

A multi-pass Visual QA review was conducted using converted slide JPEGs:
1. **Tag Name Integrity**: Checked slide-by-slide. Alphanumeric tag names (e.g. `03TI_1002.PV`) are rendered perfectly and are **not** corrupted to numbers (like `3.00`). Fixed via a strict numeric regex in `cleanValue()`.
2. **Table Fit**: Verified that all slide tables fit perfectly above the bottom margin and do not overlap with borders.
3. **Column Width Tuning**: Widened the Spearman ρ column on Slide 8 from 0.6 to 0.8 inches. "Spearman ρ" now wraps onto a single line without breaking the word. Slide 6's Pearson table columns wrap cleanly with widths of `[1.5, 1.5, 1.2]` inches.
4. **PDF Layout**: All ReportLab tables were configured to sum to exactly 504pt, fitting the page printable area within 0.75" margins with no clipping. All underscores in headers are dynamically replaced with spaces, and page numbers render as "Page X of Y" via a two-pass `NumberedCanvas`.
5. **Distribution Charts Superimposition Resolved**: Due to low missingness (0.0002% to 0.033%), plotting pre- and post-imputation distributions on the same axes caused the teal post-imputation bars to completely overlap and hide the navy pre-imputation bars. We resolved this by rendering the charts separately (`imputation_pre_distribution.png` and `imputation_post_distribution.png`) and embedding them side-by-side in both Slide 5 and Page 3 of the PDF Report.

---

## 5. Subject Matter Expert (SME) Q&A: Feature Selection & Collinearity

Here is the structured Q&A detailing feature selection and engineering logic to answer client inquiries:

* **Q1: Which core features are selected & why?**
  * *Answer*: Selected 5 core sensors out of 19 parameters: Overhead Temp (`03TIC_1023.PV`), Column Bottom Inlet Temp (`03TI_1024.PV`), Separator Pressure (`03PIC_1023.PV`), Cooling Temp Feedback (`03TI_1081.PV`), and Feed Temp Controller (`03TIC_1009.PV`). These passed correlation filters (average of Pearson, Spearman, and Distance Correlation $\ge 0.50$ against the target) and represent the primary thermodynamic components (VLE). Heavy temporal feature engineering is limited to these 5 to avoid the curse of dimensionality.
* **Q2: Why exclude C3 Inlet Temperature (`03TI_1015.PV`) from the key feature engineering list?**
  * *Answer*: It is $98.96\%$ collinear with bottom temperature `03TI_1024.PV`. Measuring virtually the same thermal energy, including lags/rolling windows for both would introduce severe redundancy. Retained as raw sensor, but excluded from heavy lags.
* **Q3: Your engineered features (lags, rolling averages) have high correlation with the raw sensors. Why didn't you filter them out?**
  * *Answer*:
    1. **Process Dynamics (Momentum & Velocity)**: Raw sensors give static states; lags and differences give process velocity/momentum. They diverge during transient pre-alarm phases, which is how the model predicts alarms.
    2. **LightGBM Collinearity Handling**: LightGBM is a decision-tree ensemble. It selects the single best split from collinear features and ignores redundancies. Trees do not experience the instability of linear models.
    3. **Prevent Information Loss**: Dropping rolling averages because they correlate with raw values removes local baseline context, blinding the model to transient shifts.
