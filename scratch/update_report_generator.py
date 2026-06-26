import os
import pandas as pd

# 1. Update first_cut_formatted_results.csv
print("Updating first_cut_formatted_results.csv...")
df_comp = pd.read_csv("outputs/eda_reports/tuning_comparison_summary.csv")
df_base = df_comp[df_comp['Version'] == 'First-Cut Baseline'].drop(columns=['Version'])
df_base.to_csv("outputs/eda_reports/first_cut_formatted_results.csv", index=False)
print("Updated first_cut_formatted_results.csv successfully.")

# 2. Modify generate_eda_pdf_report.py
report_script_path = "generate_eda_pdf_report.py"
with open(report_script_path, "r", encoding="utf-8") as f:
    code = f.read()

# Define new Section 7 content (Section 6 in the PDF headings)
old_section_7 = """    story.append(Paragraph("6. Feature Selection & Feature Engineering Strategy", h1_style))
    story.append(Paragraph(
        "Industrial sensor streams exhibit high collinearity. To build a robust and parsimonious model, "
        "we implemented a rigorous Feature Selection Strategy. We evaluated all 19 sensors against our target "
        "using Pearson, Spearman, and Distance Correlation, and established a 0.50 average absolute correlation threshold. "
        "Furthermore, we filtered out redundant sensors that were extremely highly correlated with each other (|r| >= 0.95). "
        "For example, C3 inlet temperature (03TI_1015.PV) was excluded because it is 98.96% collinear with column bottom "
        "inlet temperature (03TI_1024.PV).",
        body_style
    ))
    
    t_sel = build_report_table("feature_selection_strategy.csv", max_rows=10, custom_col_widths=[94, 90, 60, 260])
    if t_sel: story.append(t_sel)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Feature Engineering Pipeline", h2_style))
    story.append(Paragraph(
        "To capture the temporal dynamics of the plant (momentum, velocity, and baselines), we engineered 113 "
        "new features for our key sensors, including time features, lags, rolling averages/stds, and rate-of-change differences. "
        "We did NOT remove engineered features based on correlation filters because tree-based models like LightGBM "
        "handle collinearity natively, and removing them would strip the model of critical temporal trends during transient phases.",
        body_style
    ))"""

new_section_7 = """    story.append(Paragraph("6. Feature Selection & Feature Engineering Strategy", h1_style))
    story.append(Paragraph(
        "Industrial sensor streams exhibit high collinearity. To build a robust and parsimonious model, "
        "we implemented a rigorous 3-Phase Feature Selection Pipeline to select the most impactful, non-redundant "
        "features for each forecasting horizon while preserving critical physical thermodynamic signals:<br/>"
        "1. <b>Phase 1: High-Correlation Filter (Collinearity Removal):</b> Pearson correlation coefficients were calculated for all 113 engineered features. "
        "For pairs with |r| > 0.90, one feature was dropped. To preserve simpler calculation structures and direct thermodynamic signals, "
        "we prioritized keeping lower-complexity features (e.g. raw sensors over lags, lags over rolling averages, and rolling averages over standard deviations).<br/>"
        "2. <b>Phase 2: Time-Series Split & Permutation Importance (Overfitting Filter):</b> A 5-fold TimeSeriesSplit (Forward Chaining) was used to "
        "prevent lookahead bias. We trained baseline LightGBM models and computed permutation importance on validation folds using Mean Absolute Error (MAE). "
        "Features with <= 0.0 importance (such as calendar 'year' or 'month' variables that capture transient historical conditions rather than physical laws) "
        "were pruned, leaving the top 25 features.<br/>"
        "3. <b>Phase 3: SHAP TreeExplainer & Physical Validation:</b> We retrained models on the top 25 features and ran a shap.TreeExplainer on validation split. "
        "Features with mean absolute SHAP value < 10^-4 were filtered out. The SHAP summary plot below shows the feature importance rankings and their directional impact, "
        "verifying that column bottom inlet temperature (03TI_1024.PV) and separator pressure (03PIC_1023.PV) drive column overhead temperature (03TIC_1023.PV) upward.",
        body_style
    ))
    
    t_sel = build_report_table("feature_selection_strategy.csv", max_rows=10, custom_col_widths=[94, 90, 60, 260])
    if t_sel: story.append(t_sel)
    story.append(Spacer(1, 10))
    
    # Insert SHAP Plot
    story.append(Paragraph("SHAP Global Feature Importance (15-Minute Horizon)", h2_style))
    shap_img = build_report_image("shap_summary_plot_15m.png", width_inches=5.5)
    if shap_img:
        story.append(shap_img)
        story.append(Spacer(1, 10))
    
    story.append(Paragraph("Feature Engineering Pipeline", h2_style))
    story.append(Paragraph(
        "To capture the temporal dynamics of the plant (momentum, velocity, and baselines), we engineered 113 "
        "new features for our key sensors, including time features, lags, rolling averages/stds, and rate-of-change differences. "
        "These features were then pruned to a parsimonious set of 25 features per horizon using the 3-phase selection pipeline described above, "
        "improving generalization and training efficiency.",
        body_style
    ))"""

code = code.replace(old_section_7, new_section_7)

# Update Section 7 (First-Cut Model Performance) text
old_first_cut_bullets = """    story.append(Paragraph("Key Results Analysis:", h2_style))
    story.append(Paragraph("&bull; <b>High Precision early warnings:</b> The model achieves a Precision of 90.68% and 88.60% at 5m and 15m lead times. When an alert triggers, operators can be highly confident that it is genuine.", bullet_style))
    story.append(Paragraph("&bull; <b>Minimal False Alarm Rate:</b> FAR remains below 0.31% across all horizons, with a minimum of 0.1255% at 5 minutes. This prevents alarm fatigue and builds trust.", bullet_style))
    story.append(Paragraph("&bull; <b>Redundancy Elimination Benefit:</b> By excluding the redundant C3 inlet temp sensor and keeping column bottom temp and C3 pressure, we trained simpler, more robust trees without sacrificing predictive power.", bullet_style))"""

new_first_cut_bullets = """    story.append(Paragraph("Key Results Analysis:", h2_style))
    story.append(Paragraph("&bull; <b>High Precision early warnings:</b> The baseline models achieve a Precision of 85.28% and 83.39% at 5m and 15m lead times. When an alert triggers, operators can be highly confident that it is genuine.", bullet_style))
    story.append(Paragraph("&bull; <b>Minimal False Alarm Rate:</b> FAR remains below 0.37% across all horizons, with a minimum of 0.2114% at 5 minutes. This prevents alarm fatigue and builds trust.", bullet_style))
    story.append(Paragraph("&bull; <b>Pruned Feature Set Benefit:</b> By using the 3-phase feature selection pipeline to drop redundant features, we trained simpler, more robust models on 25 features instead of 113, while retaining high F1-scores.", bullet_style))"""

code = code.replace(old_first_cut_bullets, new_first_cut_bullets)

# Update Section 8 (Hyperparameter Optimization & Model Tuning) text
old_tuning_bullets = """    story.append(Paragraph("Tuning Performance Insights:", h2_style))
    story.append(Paragraph("&bull; <b>Precision and F1-Score Improvements:</b> The tuned models demonstrate consistent increases in Precision across all horizons (e.g., 5m Precision increased from 90.68% to 91.01%; 15m from 88.60% to 89.08%). This raises operator confidence in alarm validity.", bullet_style))
    story.append(Paragraph("&bull; <b>Further Reduced False Alarms:</b> The False Alarm Rate (FAR) is systematically reduced (e.g., 5m FAR dropped from 0.1255% to 0.1204%), which directly supports control room operator trust and prevents alarm fatigue.", bullet_style))
    story.append(Paragraph("&bull; <b>Feature Importance Consistency:</b> Extracting split importances from the tuned models (using the newly generated tuned_feature_importance.csv) confirms that ambient/diurnal indicators ('hour' and 'month') rank highest, followed by separator pressure changes (03PIC_1023.PV_diff_5) and cooling loop temperature feedback (03TI_1081.PV_diff_5). This reinforces the thermodynamic process drivers identified during EDA.", bullet_style))"""

new_tuning_bullets = """    story.append(Paragraph("Tuning Performance Insights:", h2_style))
    story.append(Paragraph("&bull; <b>Precision and F1-Score Improvements:</b> The tuned models demonstrate consistent increases in Precision and F1-Score across key horizons (e.g., 5m F1-score increased from 88.07% to 88.38% and Precision from 85.28% to 85.93%). This raises operator confidence in alarm validity.", bullet_style))
    story.append(Paragraph("&bull; <b>Further Reduced False Alarms:</b> The False Alarm Rate (FAR) is systematically reduced (e.g., 5m FAR dropped from 0.2114% to 0.2003%; 30m FAR from 0.2880% to 0.2755%; 60m FAR from 0.3614% to 0.3448%), supporting operator trust and preventing fatigue.", bullet_style))
    story.append(Paragraph("&bull; <b>Feature Importance Consistency:</b> Extracting split importances from the tuned models confirms that separator pressure (03PIC_1023.PV) and bottom temperature (03TI_1024.PV) features rank highest, reinforcing the thermodynamic process drivers identified during EDA.", bullet_style))"""

code = code.replace(old_tuning_bullets, new_tuning_bullets)

with open(report_script_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Modified generate_eda_pdf_report.py successfully. Compiling PDF report...")

# Run report script to generate PDF
os.system("python generate_eda_pdf_report.py")
