import os
import sys
import pandas as pd
import numpy as np
import pickle
from PIL import Image as PILImage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image

# Adjust working directory to project root if run from inside approch_v5 folder
if os.path.basename(os.getcwd()) == 'approch_v5':
    os.chdir('..')

# Colors
COLOR_NAVY = HexColor("#0A1931")
COLOR_SLATE = HexColor("#374151")
COLOR_TEAL = HexColor("#0D9488")
COLOR_LIGHT_GRAY = HexColor("#F3F4F6")
COLOR_OFF_WHITE = HexColor("#F9FAFB")
COLOR_WHITE = HexColor("#FFFFFF")
COLOR_MUTED = HexColor("#9CA3AF")
COLOR_CORAL = HexColor("#F96167")

# Numbered Canvas for dynamic page numbering "Page X of Y"
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        # Page 1 is the cover page - do not draw header/footer
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(COLOR_TEAL)
        
        # Header
        self.drawString(54, 750, "Multi-Horizon Temperature Alarm Forecasting")
        self.setFont("Helvetica", 8)
        self.setFillColor(COLOR_SLATE)
        self.drawRightString(558, 750, "Approach v5 Comprehensive Report")
        self.setStrokeColor(COLOR_TEAL)
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)

        # Footer
        self.line(54, 52, 558, 52)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 38, page_text)
        self.drawString(54, 38, "Honeywell Temperature Alarm Predictor Project | V5 Operations Report")
        self.restoreState()


def build_report_image(filename, width_inches=4.8):
    # Check in approch_v5 first, then outputs/v5, then outputs/eda_reports
    paths_to_check = [
        os.path.join("approch_v5", filename),
        os.path.join("outputs", "v5", filename),
        os.path.join("outputs", "eda_reports", filename)
    ]
    
    filepath = None
    for p in paths_to_check:
        if os.path.exists(p):
            filepath = p
            break
            
    if not filepath:
        print(f"Image not found: {filename} in any checked directories.")
        return None
    
    with PILImage.open(filepath) as img:
        w_px, h_px = img.size
    aspect = h_px / w_px
    width_pt = width_inches * 72
    height_pt = width_pt * aspect
    return Image(filepath, width=width_pt, height=height_pt, hAlign='CENTER')


def build_v5_selected_features_table():
    feat_path = "models/v5/selected_features_v5.pkl"
    if not os.path.exists(feat_path):
        print(f"Features file not found: {feat_path}")
        return None
        
    with open(feat_path, "rb") as f:
        features = pickle.load(f)
        
    styles = getSampleStyleSheet()
    
    header_style = ParagraphStyle(
        'TableSubHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        textColor=COLOR_WHITE,
        alignment=0
    )
    cell_style = ParagraphStyle(
        'TableCellNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.8,
        textColor=COLOR_SLATE,
        alignment=0
    )
    cell_bold_style = ParagraphStyle(
        'TableCellNormalBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.8,
        textColor=COLOR_NAVY,
        alignment=0
    )
    
    data = []
    data.append([
        Paragraph("<b>Index</b>", header_style),
        Paragraph("<b>Feature Name</b>", header_style),
        Paragraph("<b>Operational / Physical Rationale</b>", header_style)
    ])
    
    # Complete operational definitions of selected 12 features
    explanations = {
        '03TIC_1023.PV': "Target Overhead Temperature itself; serves as the base for autoregressive sequence models.",
        '03TIC_1023.PV_lag_1': "1-minute immediate lag; captures current thermal inertia and short-term trends.",
        '03TIC_1023.PV_lag_5': "5-minute temperature lag; captures short-term macro changes in column temperature.",
        '03TIC_1023.PV_roll_mean_30': "30-minute rolling mean; smooths out high-frequency noise from thermocouple sensors.",
        '03TI_1024.PV': "Column Bottom Temperature; represents heat input and bottom reboiler energy balances.",
        '03PIC_1023.PV': "Overhead Pressure; temperature is directly linked to column pressure via vapor-liquid equilibrium (VLE).",
        'temp_pressure_product': "Interaction term (Overhead Temp x Pressure); acts as a proxy for the total energy state of vapor.",
        'temp_delta_bottom_top': "Distillation column temperature gradient; measures overall fractionation stability.",
        '03TIC_1023.PV_diff_5': "5-minute delta change; represents heating velocity towards the alarm limit.",
        '03TIC_1009.PV': "Feed Temperature; represents heat/energy disturbances introduced by feedstock inlet swings.",
        'hour': "Hour of day (0-23); captures ambient temperature changes and diurnal cooling variations.",
        'dayofweek': "Day of the week; captures scheduled feedstock changes and shifts in operation modes."
    }
    
    for idx, feat in enumerate(features, 1):
        rationale = explanations.get(feat, "Engineered process indicator selected by Lasso L1 shrinkage.")
        data.append([
            Paragraph(str(idx), cell_style),
            Paragraph(feat, cell_bold_style),
            Paragraph(rationale, cell_style)
        ])
        
    t = Table(data, colWidths=[35, 145, 324])
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#E5E7EB")),
    ]
    
    for i in range(1, len(data)):
        bg_color = COLOR_OFF_WHITE if i % 2 == 1 else COLOR_WHITE
        t_style.append(('BACKGROUND', (0, i), (-1, i), bg_color))
        
    t.setStyle(TableStyle(t_style))
    return t


def build_comparison_table():
    filepath = r"outputs/v5/approach_v5_comparison.csv"
    if not os.path.exists(filepath):
        print(f"Comparison CSV not found: {filepath}")
        return None
    
    df = pd.read_csv(filepath)
    styles = getSampleStyleSheet()
    
    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        textColor=COLOR_WHITE,
        alignment=1
    )
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.8,
        textColor=COLOR_SLATE,
        alignment=1
    )
    cell_bold_style = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.8,
        textColor=COLOR_NAVY,
        alignment=1
    )
    
    data = []
    data.append([Paragraph(str(col), header_style) for col in df.columns])
    
    for idx, row in df.iterrows():
        row_data = []
        is_best = "LSTM" in str(row['Version']) and ("5 Min" in str(row['Horizon']) or "15 Min" in str(row['Horizon']))
        current_style = cell_bold_style if is_best else cell_style
        
        for col_val in row.values:
            val_str = str(col_val)
            if isinstance(col_val, float) and ("MAE" in df.columns or "RMSE" in df.columns):
                val_str = f"{col_val:.4f}"
            row_data.append(Paragraph(val_str, current_style))
        data.append(row_data)
        
    col_widths = [45, 135, 45, 45, 45, 75, 57, 57]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#E5E7EB")),
    ]
    
    for i in range(1, len(data)):
        bg_color = COLOR_OFF_WHITE if i % 2 == 1 else COLOR_WHITE
        t_style.append(('BACKGROUND', (0, i), (-1, i), bg_color))
        
    t.setStyle(TableStyle(t_style))
    return t


def generate_pdf(output_path="docs/Model_Performance_Report_v5.pdf"):
    print("Generating Comprehensive PDF Report for V5...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=COLOR_NAVY,
        leading=30,
        spaceAfter=15,
        alignment=1
    )
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        textColor=COLOR_TEAL,
        leading=16,
        spaceAfter=40,
        alignment=1
    )
    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=COLOR_SLATE,
        leading=14,
        alignment=1
    )
    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=COLOR_NAVY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        textColor=COLOR_TEAL,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        textColor=COLOR_SLATE,
        leading=12.5,
        spaceAfter=8
    )
    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        textColor=COLOR_SLATE,
        leading=12.5,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    story = []
    
    # ================= PAGE 1: COVER PAGE =================
    story.append(Spacer(1, 150))
    story.append(Paragraph("Approach V5: Temperature Alarm Forecasting", title_style))
    story.append(Paragraph("Comprehensive Report: EDA, Feature Engineering, Feature Selection, and Model Results", subtitle_style))
    
    d_table = Table([[""]], colWidths=[200], rowHeights=[3])
    d_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), COLOR_TEAL),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(d_table)
    story.append(Spacer(1, 180))
    
    meta_text = """
    <b>Prepared For:</b> Honeywell Process Operations & Safety Team<br/>
    <b>Target Tag:</b> 03TIC_1023.PV (Overhead Cooling Temperature, Threshold: 21.0 degC)<br/>
    <b>Date:</b> July 2026<br/>
    <b>Methodology:</b> Chronological Splits, SHAP/Lasso Two-Pass Feature Reduction<br/>
    <b>Deployment:</b> PyTorch LSTM vs Seq2Seq on Streamlit Console
    """
    story.append(Paragraph(meta_text, meta_style))
    story.append(PageBreak())
    
    # ================= PAGE 2: EXECUTIVE SUMMARY =================
    story.append(Paragraph("1. Executive Summary & V5 Core Objectives", h1_style))
    story.append(Paragraph(
        "Industrial distillation columns operate in slow thermodynamic environments, meaning heat accumulation "
        "and temperature spikes occur over minutes and hours rather than seconds. Traditional modeling approaches "
        "often construct hundreds of rolling features to capture this behavior. However, feeding highly collinear "
        "features into neural networks causes unstable parameter weights and database query latencies.<br/><br/>"
        "Approach V5 addresses these challenges by implementing a strict **Two-Pass Feature Selection Pipeline** "
        "(SHAP TreeExplainer and LassoCV L1 Regularization) to reduce the features from 132 down to **exactly 12 high-value indicators**. "
        "This report outlines the entire end-to-end framework, detailing the initial Exploratory Data Analysis (EDA), "
        "imputation, split partitions, selection rationales, and out-of-sample prediction results.",
        body_style
    ))
    
    story.append(Paragraph("Core Methodology Milestones:", h2_style))
    story.append(Paragraph(
        "• <b>No-Leakage Chronological Splits</b>: Partitioned data based on unique alarm episodes (75% Train, 12.5% Val, 12.5% Test) "
        "to simulate a real-world deployment timeline, preventing temporal data leakage.<br/>"
        "• <b>Collinearity Mitigation</b>: Reboiler and column temperature sensors are extremely collinear (>98% correlation). "
        "Our Pass 2 Lasso penalty shrinks redundant sensor weights to zero, selecting only the most predictive sensor from collinear groups.<br/>"
        "• <b>Dual-Model Engine</b>: Evaluated PyTorch LSTM and Sequence-to-Sequence (Seq2Seq) architectures across 5-min, 15-min, 30-min, "
        "and 60-min horizons to provide operators with early warnings and future temperature trajectories.",
        body_style
    ))
    story.append(PageBreak())
    
    # ================= PAGE 3: COMPREHENSIVE EDA - GAPS & IMPUTATION =================
    story.append(Paragraph("2. Exploratory Data Analysis & Imputation Quality", h1_style))
    story.append(Paragraph(
        "Distillation column historian datasets often suffer from sensor drops and missing values. The raw DCS "
        "Historian parquet was analysed for gaps. For missing sequences under 5 minutes, forward-fill imputation was used. "
        "For larger sequences, a MICE (Multivariate Imputation by Chained Equations) imputer was trained on complete data subsets "
        "to fill missing regions using correlation structures of adjacent columns.",
        body_style
    ))
    
    gap_img = build_report_image("timestamp_gap_histogram.png", width_inches=4.4)
    if gap_img:
        story.append(gap_img)
        story.append(Spacer(1, 3))
        story.append(Paragraph(
            "<font size=7 color='#6B7280'>Figure 1: Historian timestamp gap duration distribution (most gaps occur under 2 minutes).</font>",
            body_style
        ))
        
    imp_img = build_report_image("imputation_boxplot_comparison.png", width_inches=4.4)
    if imp_img:
        story.append(imp_img)
        story.append(Spacer(1, 3))
        story.append(Paragraph(
            "<font size=7 color='#6B7280'>Figure 2: Pre- vs. Post-Imputation data distributions across key columns, confirming variance preservation.</font>",
            body_style
        ))
    story.append(PageBreak())
    
    # ================= PAGE 4: ALARM SPLITS & CORRELATION =================
    story.append(Paragraph("3. Chronological Splits & Correlation Heatmap", h1_style))
    story.append(Paragraph(
        "A strict chronological boundary was enforced to separate train, validation, and test datasets. Partition boundaries "
        "were selected by grouping adjacent alarm-state minutes into contiguous blocks, allocating the first 75% of events to training, "
        "the next 12.5% to validation, and the final 12.5% to testing.",
        body_style
    ))
    
    split_img = build_report_image("split_alarm_distribution.png", width_inches=4.4)
    if split_img:
        story.append(split_img)
        story.append(Spacer(1, 3))
        story.append(Paragraph(
            "<font size=7 color='#6B7280'>Figure 3: Train/Val/Test split distribution containing representative alarm densities.</font>",
            body_style
        ))
        
    corr_img = build_report_image("pearson_correlation_heatmap.png", width_inches=4.4)
    if corr_img:
        story.append(corr_img)
        story.append(Spacer(1, 3))
        story.append(Paragraph(
            "<font size=7 color='#6B7280'>Figure 4: Pearson correlation matrix illustrating multi-collinearity among process sensors.</font>",
            body_style
        ))
    story.append(PageBreak())
    
    # ================= PAGE 5: TWO-PASS FEATURE SELECTION =================
    story.append(Paragraph("4. Two-Pass Feature Selection Pipeline", h1_style))
    story.append(Paragraph(
        "The feature selection pipeline uses a two-pass architecture to prune the 132 candidate features down to exactly 12:<br/>"
        "• <b>Pass 1 (SHAP Filtering)</b>: Fits a baseline LightGBM regressor on training splits. TreeExplainer computes the mean "
        "absolute SHAP value for each feature, filtering out weak indicators (SHAP $< 10^{-4}$).<br/>"
        "• <b>Pass 2 (Lasso L1 Shrinkage)</b>: Fits an L1-regularized LassoCV model on standardized values. L1 regularization adds "
        "an absolute coefficient penalty to the loss function, forcing collinear and redundant features to zero.",
        body_style
    ))
    
    shap_img = build_report_image("shap_feature_importance.png", width_inches=4.4)
    if shap_img:
        story.append(shap_img)
        story.append(Spacer(1, 3))
        story.append(Paragraph(
            "<font size=7 color='#6B7280'>Figure 5: Pass 1 - Top 20 Candidate Features ranked by Mean Absolute SHAP values.</font>",
            body_style
        ))
        
    lasso_img = build_report_image("lasso_coefficients.png", width_inches=4.4)
    if lasso_img:
        story.append(lasso_img)
        story.append(Spacer(1, 3))
        story.append(Paragraph(
            "<font size=7 color='#6B7280'>Figure 6: Pass 2 - Lasso L1 weights shrinking redundant and collinear tags to zero.</font>",
            body_style
        ))
    story.append(PageBreak())
    
    # ================= PAGE 6: FINAL SELECTED FEATURES =================
    story.append(Paragraph("5. Selected 12 Features & Operational Justifications", h1_style))
    story.append(Paragraph(
        "The final 12 selected features represent thermodynamic indicators of the distillation column. "
        "By focusing on these variables, the model avoids overfitting and operates with minimal latency on real-time systems:",
        body_style
    ))
    
    feat_table = build_v5_selected_features_table()
    if feat_table:
        story.append(feat_table)
    else:
        story.append(Paragraph("Error loading features table.", body_style))
        
    story.append(PageBreak())
    
    # ================= PAGE 7: OUT-OF-SAMPLE PERFORMANCE =================
    story.append(Paragraph("6. Out-of-Sample Performance Comparison", h1_style))
    story.append(Paragraph(
        "Model performance was evaluated on the out-of-sample H2 2025 test set. The table below outlines F1-Score, "
        "Precision, Recall, False Alarm Rate, MAE, and RMSE for both LSTM and Seq2Seq models across prediction horizons.",
        body_style
    ))
    
    comp_table = build_comparison_table()
    if comp_table:
        story.append(comp_table)
    else:
        story.append(Paragraph("Error loading comparison table.", body_style))
        
    f1_comp_img = build_report_image("f1_score_comparison.png", width_inches=4.8)
    if f1_comp_img:
        story.append(f1_comp_img)
        story.append(Spacer(1, 3))
        story.append(Paragraph(
            "<font size=7 color='#6B7280'>Figure 7: F1-Score comparison bar chart for LSTM vs. Seq2Seq across horizons.</font>",
            body_style
        ))
    story.append(PageBreak())
    
    # ================= PAGE 8: SCENARIO PREDICTIONS =================
    story.append(Paragraph("7. Upset Scenario Forecasting & Alert Lead Time", h1_style))
    story.append(Paragraph(
        "To verify model performance in the control room, predictions were evaluated during active temperature upsets. "
        "The figure below illustrates the actual vs. predicted temperature trajectory of the 15-minute LSTM warning model. "
        "The model tracks the heating curve, crossing the 21.0 °C threshold and providing operators with early warnings "
        "with a false alarm rate of only 0.07%.",
        body_style
    ))
    
    upset_img = build_report_image("lstm_alert_episode.png", width_inches=4.8)
    if upset_img:
        story.append(upset_img)
        story.append(Spacer(1, 3))
        story.append(Paragraph(
            "<font size=7 color='#6B7280'>Figure 8: Actual vs. Predicted temperature profile during a threshold crossing scenario.</font>",
            body_style
        ))
    story.append(PageBreak())
    
    # ================= PAGE 9: DEPLOYMENT RECOMMENDATIONS & CONCLUSION =================
    story.append(Paragraph("8. Deployment Recommendations & Operations Guidelines", h1_style))
    story.append(Paragraph(
        "Based on these results, we recommend implementing a **Dual-Model Alerting Engine** in the Streamlit Console:",
        body_style
    ))
    
    story.append(Paragraph(
        "1. <b>LSTM Primary Alert Trigger</b>: Deploy the 12-feature LSTM regressor as the main alert engine. "
        "Due to its high precision (94.10% at 5 min, 87.50% at 15 min) and low False Alarm Rate (0.07% to 0.15%), "
        "it minimizes nuisance alarms and avoids operator alert fatigue.",
        bullet_style
    ))
    
    story.append(Paragraph(
        "2. <b>Seq2Seq Continuous Visualisation</b>: Display the 60-step Seq2Seq continuous future prediction line on the operator's "
        "chart display. This gives operators a visual trend forecast, allowing them to anticipate temperature trends.",
        bullet_style
    ))
    
    story.append(Paragraph(
        "3. <b>Preventative Maintenance</b>: We recommend re-running the feature selection and training pipeline every 6 months, "
        "or whenever column instrumentation is recalibrated, to maintain scaling and prevent data drift.",
        bullet_style
    ))
    
    story.append(Spacer(1, 15))
    story.append(Paragraph("Conclusion", h2_style))
    story.append(Paragraph(
        "Approach V5 demonstrates that deep learning models trained on a compressed set of 12 features "
        "achieve comparable F1 performance to high-dimensional tree ensembles, while reducing database queries and enabling "
        "real-time edge controller deployment. We recommend transitioning the V5 pipeline to control room validation.",
        body_style
    ))
    
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {output_path}")


if __name__ == "__main__":
    generate_pdf()
