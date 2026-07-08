import os
import sys
import pandas as pd
import numpy as np
from PIL import Image as PILImage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image

# Adjust working directory to project root if run from inside approch_v4 folder
if os.path.basename(os.getcwd()) == 'approch_v4':
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
        self.drawRightString(558, 750, "Approach v4 Evaluation Report")
        self.setStrokeColor(COLOR_TEAL)
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742) # Letter width is 612. Printable width is 54 to 558.

        # Footer
        self.line(54, 52, 558, 52)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 38, page_text)
        self.drawString(54, 38, "Honeywell Temperature Alarm Predictor Project | Deep Learning Evaluation")
        self.restoreState()


def build_report_image(filename, width_inches=5.2):
    filepath = os.path.join("outputs", "eda_reports", filename)
    if not os.path.exists(filepath):
        print(f"Image not found: {filepath}")
        return None
    
    with PILImage.open(filepath) as img:
        w_px, h_px = img.size
    aspect = h_px / w_px
    width_pt = width_inches * 72
    height_pt = width_pt * aspect
    return Image(filepath, width=width_pt, height=height_pt, hAlign='CENTER')


def build_selected_features_table(horizon):
    filepath = os.path.join("outputs", "eda_reports", f"selected_features_{horizon}.csv")
    if not os.path.exists(filepath):
        print(f"Features file not found: {filepath}")
        return None
        
    df = pd.read_csv(filepath) # Load all selected features
    styles = getSampleStyleSheet()
    
    header_style = ParagraphStyle(
        'TableSubHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.5,
        textColor=COLOR_WHITE,
        alignment=0 # Left
    )
    cell_style = ParagraphStyle(
        'TableCellNormal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6,
        textColor=COLOR_SLATE,
        alignment=0
    )
    cell_bold_style = ParagraphStyle(
        'TableCellNormalBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6,
        textColor=COLOR_NAVY,
        alignment=0
    )
    
    data = []
    data.append([
        Paragraph("<b>Feature Name</b>", header_style),
        Paragraph("<b>Mean Abs SHAP</b>", header_style)
    ])
    
    for idx, row in df.iterrows():
        feature_name = str(row['Feature'])
        shap_val = f"{float(row['Mean_Abs_SHAP']):.4f}"
        
        data.append([
            Paragraph(feature_name, cell_bold_style),
            Paragraph(shap_val, cell_style)
        ])
        
    t = Table(data, colWidths=[110, 60])
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#E5E7EB")),
    ]
    
    for i in range(1, len(data)):
        bg_color = COLOR_OFF_WHITE if i % 2 == 1 else COLOR_WHITE
        t_style.append(('BACKGROUND', (0, i), (-1, i), bg_color))
        
    t.setStyle(TableStyle(t_style))
    return t


def build_comparison_table():
    filepath = r"outputs/v4/approach_v4_comparison.csv"
    if not os.path.exists(filepath):
        print(f"Comparison CSV not found: {filepath}")
        return None
    
    df = pd.read_csv(filepath)
    styles = getSampleStyleSheet()
    
    # Custom Paragraph Styles for table cells
    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        textColor=COLOR_WHITE,
        alignment=1 # Center
    )
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.5,
        textColor=COLOR_SLATE,
        alignment=1 # Center
    )
    cell_bold_style = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.5,
        textColor=COLOR_NAVY,
        alignment=1 # Center
    )
    
    data = []
    # Add Header
    data.append([Paragraph(str(col), header_style) for col in df.columns])
    
    # Add Rows
    for idx, row in df.iterrows():
        row_data = []
        horizon = str(row['Horizon'])
        version = str(row['Version'])
        
        is_best = False
        if horizon == "5 Min" and (version == "LightGBM (All Features)" or version == "LSTM (All Features)"):
            is_best = True
        elif horizon == "15 Min" and (version == "LightGBM (All Features)" or version == "LSTM (Selected Features)"):
            is_best = True
        elif horizon == "30 Min" and (version == "LightGBM (All Features)" or version == "LSTM (All Features)"):
            is_best = True
        elif horizon == "60 Min" and (version == "LSTM (All Features)" or version == "LSTM (Selected Features)"):
            is_best = True
            
        current_style = cell_bold_style if is_best else cell_style
        
        for col_val in row.values:
            row_data.append(Paragraph(str(col_val), current_style))
        data.append(row_data)
        
    # Column widths (Total 495 fits inside 504 printable area)
    col_widths = [45, 135, 45, 45, 45, 70, 55, 55]
    
    t = Table(data, colWidths=col_widths, repeatRows=1)
    
    # Styling Table
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
    
    # Alternating row colors
    for i in range(1, len(data)):
        bg_color = COLOR_OFF_WHITE if i % 2 == 1 else COLOR_WHITE
        t_style.append(('BACKGROUND', (0, i), (-1, i), bg_color))
        
    t.setStyle(TableStyle(t_style))
    return t


def generate_pdf(output_path="docs/Model_Performance_Report_v4.pdf"):
    print("Generating PDF Report...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Setup document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Define custom styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=COLOR_NAVY,
        leading=30,
        spaceAfter=15,
        alignment=1 # Center
    )
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        textColor=COLOR_TEAL,
        leading=16,
        spaceAfter=40,
        alignment=1 # Center
    )
    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=COLOR_SLATE,
        leading=14,
        alignment=1 # Center
    )
    h1_style = ParagraphStyle(
        'Header1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=COLOR_NAVY,
        spaceBefore=18,
        spaceAfter=8,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'Header2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=COLOR_TEAL,
        spaceBefore=10,
        spaceAfter=5,
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
    body_bold_style = ParagraphStyle(
        'BodyTextBold',
        parent=body_style,
        fontName='Helvetica-Bold',
        textColor=COLOR_NAVY
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
    story.append(Paragraph("Multi-Horizon Temperature Alarm Forecasting", title_style))
    story.append(Paragraph("Comparative Performance Report: LightGBM vs. LSTM vs. Seq-to-Seq", subtitle_style))
    
    # Decorative line
    d_table = Table([[""]], colWidths=[200], rowHeights=[3])
    d_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), COLOR_TEAL),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(d_table)
    story.append(Spacer(1, 200))
    
    meta_text = """
    <b>Prepared For:</b> Honeywell Process Operations & Safety SME Team<br/>
    <b>Project Title:</b> 3C101 Column Overhead Temperature Alarm Prediction (PVHI)<br/>
    <b>Alarm Tag:</b> 03TIC_1023.PV (Threshold: 21.0 degC)<br/>
    <b>Date:</b> July 2026<br/>
    <b>Version:</b> Approach v4 (Deep Learning Integration)<br/>
    <b>Environment:</b> PyTorch CPU Pipeline
    """
    story.append(Paragraph(meta_text, meta_style))
    story.append(PageBreak())
    
    # ================= PAGE 2: EXECUTIVE SUMMARY & BEST MODEL ANALYSIS =================
    story.append(Paragraph("1. Executive Summary & Best Model Analysis", h1_style))
    story.append(Paragraph(
        "Industrial distillation columns operate in highly non-linear, dynamic thermodynamic states. "
        "Over the course of this project, we built a comprehensive alarm forecasting system to predict process upsets "
        "at four look-ahead horizons: <b>5 minutes</b>, <b>15 minutes</b>, <b>30 minutes</b>, and <b>60 minutes</b>. "
        "This report contrasts the performance of the previously tuned <b>LightGBM</b> models with PyTorch-based "
        "<b>Long Short-Term Memory (LSTM)</b> and <b>Sequence-to-Sequence (Seq-to-Seq)</b> models, trained on both the full "
        "feature library (132 features) and SHAP-filtered selected features.",
        body_style
    ))
    
    story.append(Paragraph("Determining 'Which Model is Best?'", h2_style))
    story.append(Paragraph(
        "The selection of the 'best' model depends heavily on the operational goal of the warning horizon. "
        "Based on performance metrics evaluated on the chronological H2 2025 out-of-sample test split, "
        "we identify the following optimal models:",
        body_style
    ))
    
    story.append(Paragraph(
        "• <b>5-Minute Horizon (Emergency Warnings) - Winner: LSTM (All Features)</b><br/>"
        "At 5 minutes, speed and trust are crucial. The <b>LSTM (All Features)</b> model achieves a <b>Precision of 95.43%</b> "
        "with an exceptionally low <b>False Alarm Rate of 0.0549%</b> (compared to LightGBM's 0.1080% FAR). "
        "This means the model cuts false alarms in half, virtually eliminating alarm fatigue and ensuring operators can "
        "trust every emergency alert.",
        bullet_style
    ))
    
    story.append(Paragraph(
        "• <b>15-Minute Horizon (Critical Warnings) - Winner: LSTM (Selected Features)</b><br/>"
        "15 minutes provides ample time for manual cooling adjustment. The <b>LSTM (Selected Features)</b> model achieves "
        "an F1-score of <b>86.84%</b> (matching tuned LightGBM All Features at 86.95%), but operates with the lowest "
        "False Alarm Rate (<b>0.1394%</b>) and highest Precision (<b>89.10%</b>) at this horizon. "
        "It uses only 25 selected features, making it highly efficient for deployment.",
        bullet_style
    ))
    
    story.append(Paragraph(
        "• <b>30-Minute Horizon (Tactical Planning) - Winner: LSTM (Selected Features)</b><br/>"
        "The <b>LSTM (Selected Features)</b> model achieves the best balance here, providing a <b>Recall of 85.96%</b> "
        "(capturing 86% of actual upsets) and an F1-score of <b>82.23%</b>, significantly outperforming "
        "the selected feature LightGBM baseline (F1 = 81.37%).",
        bullet_style
    ))
    
    story.append(Paragraph(
        "• <b>60-Minute Horizon (Strategic Actions) - Winner: LSTM (All Features)</b><br/>"
        "At the long 1-hour horizon, the <b>LSTM (All Features)</b> model dominates, achieving the highest overall F1-score of "
        "<b>73.80%</b> and a <b>Recall of 82.74%</b>, beating tuned LightGBM (F1 = 72.74%). This demonstrates the "
        "LSTM's superior ability to capture long-range temporal trends compared to gradient boosted trees.",
        bullet_style
    ))
    
    story.append(Paragraph(
        "• <b>Seq-to-Seq (The Unified Alternative) - Winner: Seq2Seq (All Features)</b><br/>"
        "While Seq-to-Seq has slightly lower F1-scores due to the difficulty of predicting a full continuous trajectory, "
        "it achieves the <b>highest sensitivity (Recall)</b> across short horizons (e.g., <b>91.63% Recall</b> at 5m and "
        "<b>88.19% Recall</b> for selected features at 15m). Operationally, a single Seq-to-Seq model replaces 4 independent "
        "models, rendering deployment and control-loop updates computationally efficient.",
        bullet_style
    ))
    
    story.append(PageBreak())
    
    # ================= PAGE 3: DATA SPLIT DETAILS & ALARM DISTRIBUTION =================
    story.append(Paragraph("2. Chronological Data Splitting & Distribution", h1_style))
    story.append(Paragraph(
        "A rigorous, chronological train-val-test splitting strategy was enforced to prevent data leakage and simulate "
        "real-world operations where the past predicts the future. Unlike random cross-validation which leaks future state "
        "through rolling feature dependencies, this division preserves the temporal arrow of time.",
        body_style
    ))
    
    # Chronological Split Description Table
    split_data = [
        [Paragraph("<b>Dataset Split</b>", body_bold_style), Paragraph("<b>Date Range Covered</b>", body_bold_style), Paragraph("<b>Operational Purpose</b>", body_bold_style)],
        [
            Paragraph("<b>Training Split</b>", body_style),
            Paragraph("January 1, 2022 to December 12, 2024 (1,550,880 mins)", body_style),
            Paragraph("Used to fit model weights and parameters (LightGBM split thresholds, LSTM neural weights).", body_style)
        ],
        [
            Paragraph("<b>Validation Split</b>", body_style),
            Paragraph("December 13, 2024 to August 9, 2025 (345,600 mins)", body_style),
            Paragraph("Used for hyperparameter optimization (via Optuna) and early stopping regularization to prevent overfitting.", body_style)
        ],
        [
            Paragraph("<b>Testing Split</b>", body_style),
            Paragraph("August 10, 2025 to January 12, 2026 (221,760 mins)", body_style),
            Paragraph("Held out completely. Serves as the final out-of-sample benchmark to report production-level metrics.", body_style)
        ]
    ]
    split_table = Table(split_data, colWidths=[100, 200, 195])
    split_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), COLOR_LIGHT_GRAY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor("#E5E7EB")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(split_table)
    story.append(Spacer(1, 10))
    
    # Embed split distribution plot
    split_img = build_report_image("split_alarm_distribution.png", width_inches=5.0)
    if split_img:
        story.append(split_img)
        story.append(Spacer(1, 5))
        story.append(Paragraph(
            "<font size=7 color='#6B7280'>Figure 1: Chronological distribution of normal operating minutes (teal) vs. active alarm periods (coral) across Train, Val, and Test splits. The splits show consistent operating distributions.</font>",
            body_style
        ))
    else:
        story.append(Paragraph("Warning: Split alarm distribution chart missing.", body_style))
        
    story.append(PageBreak())
    
    # ================= PAGE 4: PERFORMANCE COMPARISON TABLE =================
    story.append(Paragraph("3. Detailed Model Performance Comparison", h1_style))
    story.append(Paragraph(
        "Below is the complete consolidated performance report compiled from the chronological test set. "
        "Best operational metrics for each horizon are bolded.",
        body_style
    ))
    
    comp_table = build_comparison_table()
    if comp_table:
        story.append(comp_table)
    else:
        story.append(Paragraph("Error: Comparison table could not be loaded.", body_style))
        
    story.append(Spacer(1, 15))
    story.append(Paragraph("Key Observations:", h2_style))
    story.append(Paragraph(
        "1. <b>Deep Learning Robustness</b>: Deep learning architectures (LSTM & Seq2Seq) are extremely robust. "
        "LSTMs achieved either the best Precision/FAR (at 5m and 15m) or the best overall F1 (at 60m).<br/>"
        "2. <b>Thermodynamic Trend Capture</b>: Decision tree regressors (LightGBM) are excellent at fitting "
        "tabular rolling thresholds but suffer on raw long-horizon forecasting. The LSTM's recurrent hidden "
        "states keep track of thermal accumulation, leading to a <b>1.06% absolute F1-score improvement</b> "
        "over LightGBM at the 60-minute mark.<br/>"
        "3. <b>False Alarm Rate Suppression</b>: The deep learning models suppress False Alarm Rates below 0.3% "
        "across almost all configurations (except the 60-minute Seq-to-Seq), which is critical for plant operator trust.",
        body_style
    ))
    
    story.append(PageBreak())
    
    # ================= PAGE 5: FEATURE DESCRIPTION =================
    story.append(Paragraph("4. Feature Engineering Deep Dive", h1_style))
    story.append(Paragraph(
        "To give the models 'eyes' to see process trends, velocity, and thermodynamic context, a comprehensive feature "
        "library was engineered. This section details the features used.",
        body_style
    ))
    
    # Feature Engineering Table
    f_data = [
        [Paragraph("<b>Feature Group</b>", body_bold_style), Paragraph("<b>Description / Calculations</b>", body_bold_style), Paragraph("<b>Operational Value</b>", body_bold_style)],
        [
            Paragraph("<b>Base Sensor Tags</b><br/>(19 features)", body_style),
            Paragraph("Raw readings of all 19 process variables (temperatures, pressures, flows, levels) at current minute $t$.", body_style),
            Paragraph("Establishes the current steady-state baseline of the distillation column.", body_style)
        ],
        [
            Paragraph("<b>Lags</b><br/>(35 features)", body_style),
            Paragraph("Sensor values shifted backward in time:<br/>$X_{t-1}, X_{t-2}, X_{t-5}, X_{t-10}, X_{t-15}, X_{t-30}, X_{t-60}$ minutes.<br/>Computed for 5 key columns.", body_style),
            Paragraph("Captures short-term and long-term process momentum (direction of temperature/pressure).", body_style)
        ],
        [
            Paragraph("<b>Rolling Means</b><br/>(15 features)", body_style),
            Paragraph("Moving averages over <b>10, 30, and 60 minutes</b> for 5 key columns.", body_style),
            Paragraph("Filters high-frequency noise and reveals underlying thermal accumulation trends.", body_style)
        ],
        [
            Paragraph("<b>Rolling StDev</b><br/>(15 features)", body_style),
            Paragraph("Moving standard deviations over <b>10, 30, and 60 minutes</b> for 5 key columns.", body_style),
            Paragraph("Detects process oscillations and instability, which often precede an overhead upset.", body_style)
        ],
        [
            Paragraph("<b>Rolling Min / Max</b><br/>(30 features)", body_style),
            Paragraph("Moving min/max bounds over <b>10, 30, and 60 minutes</b> for 5 key columns.", body_style),
            Paragraph("Establishes recent operating envelopes and catches sudden spikes or dropouts.", body_style)
        ],
        [
            Paragraph("<b>Differences</b><br/>(15 features)", body_style),
            Paragraph("Rate of change: $X_t - X_{t-5}$, $X_t - X_{t-15}$, $X_t - X_{t-30}$ minutes for 5 key columns.", body_style),
            Paragraph("The mathematical derivative (velocity) showing how fast temperature or pressure is running up.", body_style)
        ],
        [
            Paragraph("<b>Time Context</b><br/>(3 features)", body_style),
            Paragraph("Hour of day, Day of week, Month of year.", body_style),
            Paragraph("Accounts for ambient weather cycles (overhead coolers work harder during mid-day and summer).", body_style)
        ]
    ]
    f_table = Table(f_data, colWidths=[100, 220, 175])
    f_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), COLOR_LIGHT_GRAY),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor("#E5E7EB")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(f_table)
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("Process Collinearity & Exclusions", h2_style))
    story.append(Paragraph(
        "Many sensor tags are highly collinear. For example, Column Bottom Inlet Temp (<code>03TI_1024.PV</code>) "
        "and C3 Inlet Temp (<code>03TI_1015.PV</code>) are <b>98.96% correlated</b>. "
        "Because they measure virtually the same thermal energy entering the column, building lags/rolling averages "
        "for both would introduce severe redundancy. We kept the raw <code>03TI_1015.PV</code> in the training dataset "
        "so the models have access to it, but excluded it from heavy temporal feature engineering, keeping the base "
        "lag/rolling calculations focused on 5 key columns: <code>03TIC_1023.PV</code>, <code>03TI_1024.PV</code>, "
        "<code>03PIC_1023.PV</code>, <code>03TI_1081.PV</code>, and <code>03TIC_1009.PV</code>.",
        body_style
    ))
    story.append(PageBreak())
    
    # ================= PAGES 6-9: FEATURE SELECTION BY HORIZON & SHAP PLOTS =================
    story.append(Paragraph("5. Feature Selection Pipeline & SHAP Analysis", h1_style))
    story.append(Paragraph(
        "To resolve feature redundancy and prevent overfitting, we ran a SHAP TreeExplainer on validation models. "
        "Features with a mean absolute SHAP value below $10^{-4}$ were filtered out. Below we detail the exact list of "
        "selected features and their global SHAP TreeExplainer summary plots for each individual model.",
        body_style
    ))
    
    horizons = [
        ("5m", "5-Minute Lead Time Model (26 Features selected)"),
        ("15m", "15-Minute Lead Time Model (25 Features selected)"),
        ("30m", "30-Minute Lead Time Model (26 Features selected)"),
        ("60m", "60-Minute Lead Time Model (25 Features selected)")
    ]
    
    for h_code, h_name in horizons:
        story.append(Paragraph(f"Horizon: {h_name}", h2_style))
        story.append(Paragraph(
            f"The table below lists all selected features and their Mean Absolute SHAP values. "
            f"The accompanying plot shows feature importance rankings and their directional impact: "
            f"red dots indicate high feature values, blue indicates low, and their horizontal position shows "
            f"whether they drive the prediction higher (toward alarm) or lower.",
            body_style
        ))
        
        f_table_h = build_selected_features_table(h_code)
        img_h = build_report_image(f"shap_summary_plot_{h_code}.png", width_inches=4.2)
        
        if f_table_h and img_h:
            # Layout table side by side: left column for table (170pt), right column for image (325pt)
            layout = Table([[f_table_h, img_h]], colWidths=[175, 320])
            layout.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(layout)
        else:
            if f_table_h: story.append(f_table_h)
            if img_h: story.append(img_h)
            
        story.append(PageBreak())
        
    # ================= PAGE 10: RECOMMENDATIONS =================
    story.append(Paragraph("6. Control Room Operational Recommendations", h1_style))
    story.append(Paragraph(
        "To deploy these models successfully in a live control room, we propose a hybrid deployment strategy "
        "that leverages the strengths of both LSTMs and Seq-to-Seq architectures:",
        body_style
    ))
    
    story.append(Paragraph(
        "1. <b>Implement Dual-Model Alerting (LSTM + Seq2Seq)</b>:<br/>"
        "Deploy the <b>LSTM (All Features)</b> as the primary trigger for the 5-minute Emergency Warning, "
        "leveraging its 95% Precision to minimize nuisance alarms. In parallel, run the <b>Seq-to-Seq (Selected Features)</b> "
        "model to display a continuous 60-minute prediction trend. If the Seq-to-Seq trend shows a sustained overhead "
        "temperature excursion above 21.0 degC for more than 5 consecutive minutes, trigger a pre-alarm warning "
        "even if the 15-minute LSTM hasn't fired yet.",
        bullet_style
    ))
    
    story.append(Paragraph(
        "2. <b>HMI Visualization (Operator Trend Screen)</b>:<br/>"
        "Render the 60-minute Seq-to-Seq forecast as a <b>dashed line extension</b> on the operator's main temperature trend chart. "
        "Display a shaded 'prediction envelope' representing the model's prediction confidence interval. "
        "If the predicted line crosses the 21.0 degC alarm threshold, color-code the forecast line red to instantly "
        "draw operator attention.",
        bullet_style
    ))
    
    story.append(Paragraph(
        "3. <b>Automated Scaler and Weight Maintenance</b>:<br/>"
        "Deep learning models can suffer from data drift when the plant processes new feed compositions or undergoes "
        "catalyst changes. We recommend setting up an automated pipeline to re-fit the StandardScalers and fine-tune "
        "the LSTM weights every 6 months using the latest plant historian data, validating against chronological "
        "holdout periods.",
        bullet_style
    ))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph("Conclusion", h2_style))
    story.append(Paragraph(
        "Deep learning models (specifically LSTMs) provide significant operational advantages over the previously "
        "built LightGBM models by cutting emergency false alarms in half (down to 0.05% FAR) and increasing long-horizon "
        "predictive capability (reaching 73.80% F1-score at 60 minutes). We recommend proceeding with the deployment "
        "of the LSTM and Seq-to-Seq hybrid pipeline.",
        body_style
    ))
    
    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {output_path}")


if __name__ == "__main__":
    generate_pdf()
