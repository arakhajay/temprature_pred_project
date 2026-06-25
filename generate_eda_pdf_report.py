import os
import pandas as pd
from PIL import Image as PILImage
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether

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
        self.setFont("Helvetica", 8)
        self.setFillColor(COLOR_SLATE)

        # Header
        self.drawString(54, 750, "Advanced Process Exploratory Data Analysis (EDA) Report")
        self.setStrokeColor(COLOR_TEAL)
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742) # Letter width is 612pt. Margins are 54pt. Printable width is 504pt (from 54 to 558).

        # Footer
        self.line(54, 52, 558, 52)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 38, page_text)
        self.drawString(54, 38, "Honeywell Temperature Alarm Predictor Project | DCS Historian Analysis")
        self.restoreState()


# Table Formatter helper
def build_report_table(filename, max_rows=None, custom_col_widths=None):
    filepath = os.path.join("outputs", "eda_reports", filename)
    if not os.path.exists(filepath):
        print(f"CSV file not found: {filepath}")
        return None
    
    df = pd.read_csv(filepath)
    if max_rows is not None:
        df = df.head(max_rows)
    if custom_col_widths is not None:
        df = df.iloc[:, :len(custom_col_widths)]
        
    styles = getSampleStyleSheet()
    
    # Custom Paragraph Styles for table cells
    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        textColor=COLOR_WHITE,
        alignment=1 # Center
    )
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        textColor=COLOR_SLATE,
        alignment=1 # Center
    )
    
    data = []
    # Add Header
    data.append([Paragraph(str(col).replace('_', ' '), header_style) for col in df.columns])
    
    # Add Rows
    for _, row in df.iterrows():
        row_cells = []
        for val in row:
            text = str(val)
            # Float clean-up
            try:
                float_val = float(val)
                if float_val.is_integer():
                    text = str(int(float_val))
                elif "Pct" in df.columns or "rate" in text.lower() or "corr" in filename.lower() or float_val < 1:
                    text = f"{float_val:.4f}"
                else:
                    text = f"{float_val:.2f}"
            except ValueError:
                pass
            row_cells.append(Paragraph(text, cell_style))
        data.append(row_cells)
        
    t = Table(data, colWidths=custom_col_widths, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_NAVY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, COLOR_LIGHT_GRAY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COLOR_WHITE, COLOR_OFF_WHITE])
    ]))
    return t


# Image Scaler helper
def build_report_image(filename, width_inches=5.5):
    filepath = os.path.join("outputs", "eda_reports", filename)
    if not os.path.exists(filepath):
        print(f"Image not found: {filepath}")
        return None
    
    with PILImage.open(filepath) as img:
        w_px, h_px = img.size
    aspect = h_px / w_px
    width_pt = width_inches * 72
    height_pt = width_pt * aspect
    return Image(filepath, width=width_pt, height=height_pt, hAlign='LEFT')


def generate_pdf():
    pdf_path = os.path.join("docs", "EDA_Detailed_Report.pdf")
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    # 54pt margin = 0.75". Page is 612x792. Printable width is 504pt.
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Document Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        textColor=COLOR_NAVY,
        spaceAfter=15,
        leading=32
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=12,
        textColor=COLOR_TEAL,
        spaceAfter=30,
        leading=16
    )
    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=COLOR_NAVY,
        spaceBefore=20,
        spaceAfter=10,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=COLOR_TEAL,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=COLOR_SLATE,
        spaceBefore=4,
        spaceAfter=8,
        leading=14
    )
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        textColor=COLOR_SLATE,
        leftIndent=15,
        spaceBefore=2,
        spaceAfter=2,
        leading=13
    )
    metadata_style = ParagraphStyle(
        'Metadata',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        textColor=COLOR_SLATE,
        leading=14
    )

    story = []
    
    # ============================================================================
    # Page 1: Cover Page
    # ============================================================================
    story.append(Spacer(1, 100))
    story.append(Paragraph("HONEYWELL DCS HISTORIAN ANALYSIS", subtitle_style))
    story.append(Paragraph("Advanced Process Exploratory<br/>Data Analysis (EDA) Report", title_style))
    story.append(Spacer(1, 10))
    
    # Decorative line
    story.append(Table(
        [['']], 
        colWidths=[504], 
        rowHeights=[4], 
        style=TableStyle([('BACKGROUND', (0,0), (-1,-1), COLOR_TEAL)])
    ))
    story.append(Spacer(1, 120))
    
    # Metadata block
    metadata_text = """
    <b>Prepared by:</b> Data Science & Process Analytics Team<br/>
    <b>Date:</b> June 2026<br/>
    <b>Target Tag:</b> 03TIC_1023.PV (Column Overhead Temperature)<br/>
    <b>Safety Threshold:</b> PVHI &ge; 21.0 &deg;C<br/>
    <b>Data Span:</b> Jan 2022 to Jan 2026 (4 Widescreen Years)<br/>
    <b>Data Volume:</b> 2,019,221 continuous records (minutes)
    """
    story.append(Paragraph(metadata_text, metadata_style))
    story.append(PageBreak())
    
    # ============================================================================
    # Section 1: Executive Summary
    # ============================================================================
    story.append(Paragraph("Executive Summary", h1_style))
    story.append(Paragraph(
        "This diagnostic report provides a comprehensive evaluation of the historical process values "
        "associated with the overhead distillation column temperature alarm (tag 03TIC_1023.PV). Over the "
        "4-year continuous operational period, the column recorded 1,561 safety violations where the "
        "temperature met or exceeded the PVHI threshold of 21.0°C. By applying advanced exploratory "
        "data analysis methods—specifically consecutive null audits, triple correlation matrices (Pearson, "
        "Spearman, and Distance correlation), alarm duration buckets, and pre/post-alarm ramping dynamics—we "
        "uncovered critical process characteristics. These insights directly inform the design of our "
        "multi-horizon predictive alarm models and identify clear process bottlenecks.",
        body_style
    ))
    story.append(Paragraph("Key Findings:", h2_style))
    story.append(Paragraph("&bull; <b>Data Quality & Imputation:</b> Missing data rates are extremely low (<0.15%). Since all tags fell well below the 60% missingness threshold, a 5-minute capped forward-fill was successfully applied, preserving the raw physical distributions without introducing synthetic bias.", bullet_style))
    story.append(Paragraph("&bull; <b>Non-Linear Thermodynamics:</b> Multi-method correlations revealed large discrepancies (>0.30) between linear Pearson coefficients and Spearman/Distance correlation. These hidden statistical dependencies validate the use of non-linear LightGBM tree models over standard linear regressions.", bullet_style))
    story.append(Paragraph("&bull; <b>Downtime Drivers:</b> Sustained thermal upsets (60+ mins) represent only 13.7% of events but drive 87.8% of total alarm downtime. Conversely, chattering alarms (≤1 min) represent 19.5% of events but contribute less than 0.7% of downtime, flagging them for isolation.", bullet_style))
    story.append(Paragraph("&bull; <b>Thermodynamic Lead:</b> Column bottom inlet temperature (03TI_1024.PV) ramps at a higher rate (+0.0155°C/min) than the overhead temp (+0.0132°C/min) preceding alarms, proving that heat rise starts at the bottom and works upward.", bullet_style))
    story.append(Paragraph("&bull; <b>Ambient Influence:</b> Alarm rates peak during the summer months (June-August). This is directly related to high ambient air temperatures reducing the heat exchange efficiency of the overhead cooling condenser.", bullet_style))
    story.append(Spacer(1, 15))
    
    # ============================================================================
    # Section 2: Data Quality & Missingness Analysis
    # ============================================================================
    story.append(Paragraph("1. Data Quality & Missingness Analysis", h1_style))
    story.append(Paragraph(
        "Industrial DCS historian logs are prone to telemetry dropouts, sensor drift, and shutdown gaps. "
        "Before constructing predictive models, we performed a thorough missingness audit to evaluate "
        "reindexing and imputation constraints.",
        body_style
    ))
    
    story.append(Paragraph("Completeness Overview", h2_style))
    story.append(Paragraph(
        "Reindexing the data to a strict 1-minute grid exposed gaps. The overall dataset completeness is "
        "exceptional, averaging 99.96% across all 19 sensors. Gaps corresponding to the 85 plant trips "
        "had already been pre-removed from the source parquet, leaving clear timestamp jumps which we isolated "
        "as NaN rows to prevent temporal leakage in rolling averages.",
        body_style
    ))
    
    img1 = build_report_image("null_percentages.png", width_inches=5.2)
    if img1: story.append(img1)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Consecutive Null Durations", h2_style))
    story.append(Paragraph(
        "Analyzing consecutive nulls separates transient sensor noise from systemic disconnects. Only three tags "
        "showed significant gaps. Tag <b>03TI_1002.PV</b> suffered the largest consecutive drop in the dataset—a "
        "single gap of 2,224 rows (~37 hours), likely representing an instrument swap or calibration shut-off. "
        "All other 16 tags displayed maximum consecutive null lengths of 10 minutes or fewer.",
        body_style
    ))
    
    img2 = build_report_image("consecutive_null_boxplot.png", width_inches=5.2)
    if img2: story.append(img2)
    story.append(Spacer(1, 10))
    
    t1 = build_report_table("consecutive_null_aggregated.csv", max_rows=5, custom_col_widths=[114, 75, 75, 75, 75, 90])
    if t1: story.append(t1)
    
    story.append(PageBreak())
    
    # ============================================================================
    # Section 2 (Cont.): Imputation Strategy
    # ============================================================================
    story.append(Paragraph("Conditional Imputation Strategy", h2_style))
    story.append(Paragraph(
        "To handle missing rows, we established a conditional rule: if a column has consecutive missing values "
        "exceeding 60 minutes, MICE is used to reconstruct the state from other tags. If 60 minutes or below, "
        "Forward-Fill and Backward-Fill (FFill+BFill) are applied. In this dataset, two columns (03TI_1002.PV and "
        "02FI_1000.PV) had consecutive gaps exceeding 60 minutes and were imputed using MICE. All other 17 columns "
        "had short consecutive gaps (≤ 10 minutes) and were imputed using forward-fill followed by backward-fill, "
        "ensuring all dropouts were resolved without introducing synthetic bias.",
        body_style
    ))
    
    img_zoom = build_report_image("imputation_zoom_line.png", width_inches=2.45)
    img_box = build_report_image("imputation_boxplot_comparison.png", width_inches=2.45)
    if img_zoom and img_box:
        img_table = Table([[img_zoom, img_box]], colWidths=[252, 252])
        img_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0)
        ]))
        story.append(img_table)
    story.append(Spacer(1, 10))
    
    t2 = build_report_table("imputation_strategy.csv", max_rows=5, custom_col_widths=[114, 75, 75, 240])
    if t2: story.append(t2)
    
    story.append(Spacer(1, 15))
    
    # ============================================================================
    # Section 3: Multi-Method Correlation Analysis
    # ============================================================================
    story.append(Paragraph("2. Multi-Method Correlation Analysis", h1_style))
    story.append(Paragraph(
        "Standard industrial analyses rely on Pearson linear correlation. However, chemical columns exhibit "
        "highly non-linear behaviors under dynamic load changes. We ran Pearson, Spearman (rank-order), "
        "and Distance Correlation (non-linear independence check) to establish clean process relationships.",
        body_style
    ))
    
    story.append(Paragraph("Collinear Inter-Variable Pairs (excluding Target)", h2_style))
    story.append(Paragraph(
        "Pearson correlation identifies proportional changes. Spearman correlation detects monotonic rank changes. "
        "Highly collinear inter-variable pairs (|r| ≥ 0.80) excluding the target tag (such as 03TI_1015.PV and 03TI_1024.PV at r = 0.9896) "
        "represent redundant physical sensors. These are flagged for potential removal by the Subject Matter Expert (SME) "
        "to prevent multicollinearity and simplify the feature space for training models.",
        body_style
    ))
    
    img4 = build_report_image("pearson_correlation_heatmap.png", width_inches=5.2)
    if img4: story.append(img4)
    story.append(Spacer(1, 10))
    
    t3 = build_report_table("pearson_inter_variable_high_correlation_pairs.csv", max_rows=5, custom_col_widths=[184, 80, 80, 160])
    if t3: story.append(t3)
    
    story.append(PageBreak())
    
    # ============================================================================
    # Section 3 (Cont.): Distance Correlation
    # ============================================================================
    story.append(Paragraph("Distance Correlation & Target Rankings", h2_style))
    story.append(Paragraph(
        "Distance Correlation (dcor) captures arbitrary non-linear statistical dependencies. The target "
        "column temperature (03TIC_1023.PV) is highly dependent on bottom temperatures and separator pressures. "
        "03TI_1024.PV (bottom inlet) and 03TI_1015.PV (C3 inlet) have the highest distance correlations (0.966 and 0.962). "
        "03PIC_1023.PV (separator pressure) ranks 4th, highlighting the thermodynamic pressure-temperature connection.",
        body_style
    ))
    
    img5 = build_report_image("distance_correlation_heatmap.png", width_inches=5.2)
    if img5: story.append(img5)
    story.append(Spacer(1, 10))
    
    img6 = build_report_image("target_correlation_rankings.png", width_inches=5.2)
    if img6: story.append(img6)
    story.append(Spacer(1, 10))
    
    t4 = build_report_table("target_correlation_rankings.csv", max_rows=6, custom_col_widths=[144, 90, 90, 90, 90])
    if t4: story.append(t4)
    
    story.append(PageBreak())
    
    # ============================================================================
    # Section 4: Alarm Characteristics & Sensor Noise
    # ============================================================================
    story.append(Paragraph("3. Alarm Characteristics & Sensor Noise", h1_style))
    story.append(Paragraph(
        "Control room operators face severe alarm fatigue when sensors chattered. We analyzed "
        "the 1,561 alarm crossings to isolate process noise from genuine thermal upsets.",
        body_style
    ))
    
    story.append(Paragraph("Alarm Duration Buckets", h2_style))
    story.append(Paragraph(
        "The distribution of alarm durations is heavily skewed. Sub-minute alarm crossings (chattering) "
        "make up 19.47% of all events (304 episodes) but represent only 304 minutes of total cumulative downtime. "
        "In contrast, sustained thermal events (60+ minutes) represent only 13.71% of episodes (214 events) but "
        "drive **87.8% of all alarm downtime** (53,829 minutes). The longest single alarm lasted 561 minutes (~9 hours).",
        body_style
    ))
    
    img7 = build_report_image("alarm_duration_histogram.png", width_inches=5.2)
    if img7: story.append(img7)
    story.append(Spacer(1, 10))
    
    t5 = build_report_table("alarm_duration_buckets.csv", max_rows=6, custom_col_widths=[144, 100, 130, 130])
    if t5: story.append(t5)
    
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Chattering Isolation", h2_style))
    story.append(Paragraph(
        "We defined chattering sequences as alarm crossings ≤ 1 minute in duration, separated by less than 5 minutes "
        "of normal operation. We identified 360 chattering sequences representing localized loop noise. "
        "By filtering these sequences out, we can reduce false alarms and focus predictive models on forecasting "
        "moderate (5-15m) and sustained (60m+) thermal run-ups.",
        body_style
    ))
    
    img8 = build_report_image("alarm_duration_windowing.png", width_inches=5.2)
    if img8: story.append(img8)
    
    story.append(PageBreak())
    
    # ============================================================================
    # Section 5: Transient System Thermodynamics
    # ============================================================================
    story.append(Paragraph("4. Transient System Thermodynamics", h1_style))
    story.append(Paragraph(
        "To establish warning lead times, we evaluated the rates of change preceding and following "
        "the 1,561 alarm events.",
        body_style
    ))
    
    story.append(Paragraph("Pre-Alarm Ramping Rates", h2_style))
    story.append(Paragraph(
        "Analyzing a 30-minute window before alarm onset shows clear leading thermodynamic indicators. "
        "Overhead temperature (03TIC_1023.PV) ramps at +0.0132°C/min (+0.39°C over 30m). Column bottom "
        "inlet temperature (03TI_1024.PV) ramps at **+0.0155°C/min** (+0.47°C over 30m), demonstrating "
        "that heat accumulates at the column base and rises upward. Separator pressure (03PIC_1023.PV) "
        "shows early accumulation at +0.0021 barg/min.",
        body_style
    ))
    
    img9 = build_report_image("pre_alarm_roc_heatmap.png", width_inches=5.2)
    if img9: story.append(img9)
    story.append(Spacer(1, 10))
    
    t6 = build_report_table("pre_alarm_behavior_30m.csv", max_rows=5, custom_col_widths=[144, 90, 90, 90, 90])
    if t6: story.append(t6)
    
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Post-Trip Verification", h2_style))
    story.append(Paragraph(
        "Startups after plant shutdowns can cause thermal spikes. We cross-referenced the 85 trip end times "
        "with alarm onset. Only 12 of the 1,561 alarms occurred within 120 minutes of startup, proving "
        "that start-up thermal transients are stable and do not cause false alarms.",
        body_style
    ))
    
    t7 = build_report_table("post_trip_alarm_verification.csv", max_rows=6, custom_col_widths=[114, 90, 114, 114, 72])
    if t7: story.append(t7)
    
    story.append(PageBreak())
    
    # ============================================================================
    # Section 6: Seasonal Trends & Split Distributions
    # ============================================================================
    story.append(Paragraph("5. Seasonal & Split Distributions", h1_style))
    story.append(Paragraph(
        "Finally, we analyzed seasonal trends to optimize plant maintenance and checked chronological split "
        "balance to secure offline model evaluations.",
        body_style
    ))
    
    story.append(Paragraph("Seasonal Alarm Trends", h2_style))
    story.append(Paragraph(
        "Alarms display strong seasonal patterns, peaking during summer (June-August). High ambient "
        "air temperatures reduce the heat exchange efficiency of the overhead cooling condenser, causing "
        "heat buildup. Decoking and cleaning the condensers should be scheduled before summer (May) to maximize "
        "thermal headroom.",
        body_style
    ))
    
    img10 = build_report_image("monthly_seasonal_trends.png", width_inches=5.2)
    if img10: story.append(img10)
    story.append(Spacer(1, 10))
    
    t8 = build_report_table("yearly_alarm_summary.csv", max_rows=5, custom_col_widths=[80, 100, 114, 114, 96])
    if t8: story.append(t8)
    
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Evaluating Data Split Balance", h2_style))
    story.append(Paragraph(
        "To ensure robust offline testing, we validated that alarm episodes are properly balanced across the partitions: "
        "Train split contains 1,169 episodes (74.89% of events), Val split contains 199 episodes (12.75% of events), "
        "and Test split contains 193 episodes (12.36% of events). This distribution closely matches the client's "
        "requested 75/12.5/12.5 split and ensures that offline validation will be highly representative of live plant performance.",
        body_style
    ))
    
    img11 = build_report_image("split_alarm_distribution.png", width_inches=5.2)
    if img11: story.append(img11)
    story.append(Spacer(1, 10))
    
    t9 = build_report_table("split_alarm_distribution.csv", max_rows=3, custom_col_widths=[114, 90, 80, 80, 100])
    if t9: story.append(t9)
    
    story.append(PageBreak())
    
    # ============================================================================
    # Section 7: Feature Selection & Feature Engineering
    # ============================================================================
    story.append(Paragraph("6. Feature Selection & Feature Engineering Strategy", h1_style))
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
    ))
    
    t_eng = build_report_table("feature_engineering_pipeline.csv", max_rows=6, custom_col_widths=[104, 50, 110, 240])
    if t_eng: story.append(t_eng)
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("Subject Matter Expert (SME) Q&A", h2_style))
    story.append(Paragraph(
        "<b>Q1: On which core features did you build new features (lags, rolling stats), and why?</b><br/>"
        "We selected 5 key sensors out of the 19 raw process parameters to build our 113 engineered features: "
        "Overhead Temp (03TIC_1023.PV), Column Bottom Inlet Temp (03TI_1024.PV), Separator Pressure (03PIC_1023.PV), "
        "Cooling Temp Feedback (03TI_1081.PV), and Feed Temp Controller (03TIC_1009.PV). "
        "These 5 core sensors passed our correlation filters (average of Pearson, Spearman, and Distance Correlation >= 0.50 against the target) "
        "and represent the primary thermodynamic components of the system. Heavy temporal feature engineering was limited to these 5 key sensors "
        "to prevent the curse of dimensionality (overfitting, slow training, and noise) that would occur if we engineered features on all 19 sensors.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Q2: Why did you exclude C3 Inlet Temperature (03TI_1015.PV) from the key feature engineering list?</b><br/>"
        "03TI_1015.PV is 98.96% collinear with bottom temperature 03TI_1024.PV. Because they measure virtually the same thermal energy entering the column, "
        "building lags/rolling averages for both would introduce severe redundancy. We kept the raw 03TI_1015.PV in the training dataset so the model has "
        "access to it, but excluded it from heavy temporal feature engineering.",
        body_style
    ))
    story.append(Paragraph(
        "<b>Q3: Your engineered features (lags, rolling averages) have high correlation with the raw sensors. Why didn't you filter them out?</b><br/>"
        "1. <i>Process Dynamics (Momentum & Velocity):</i> Raw sensors give static snapshots (e.g. 'temp is 20°C'). A difference gives the velocity of "
        "the temperature rise. A rolling average gives the local operating baseline. Tree-based models (like LightGBM) split on these features to "
        "identify transient phases (e.g., rapid temperature ramping preceding an alarm), which are physically distinct from steady-state normal operations.<br/>"
        "2. <i>LightGBM Collinearity Handling:</i> Unlike linear models, LightGBM is a decision-tree ensemble. It selects the single best feature split "
        "that maximizes information gain and ignores redundant collinear features. It does not suffer from numerical instability in the presence of multicollinearity.<br/>"
        "3. <i>Preventing Information Loss:</i> Dropping rolling averages because they correlate with raw values removes local baseline context, blinding "
        "the model to transient shifts.",
        body_style
    ))
    
    story.append(PageBreak())
    
    # ============================================================================
    # Section 8: First-Cut Model Performance
    # ============================================================================
    story.append(Paragraph("7. First-Cut Model Performance", h1_style))
    story.append(Paragraph(
        "Using our engineered features and chronological data splits, we trained four independent LightGBM models "
        "to forecast temperature alarm crossings (>= 21.0°C) at 5m, 15m, 30m, and 60m horizons. Performance was evaluated "
        "on the held-out H2 2025 Test Set (July 2025 to Jan 2026). The results demonstrate high precision at short lead times "
        "and a False Alarm Rate (FAR) below 0.5% across all horizons, successfully mitigating control room alarm fatigue.",
        body_style
    ))
    
    t_res = build_report_table("first_cut_formatted_results.csv", max_rows=5, custom_col_widths=[72, 72, 72, 72, 86, 65, 65])
    if t_res: story.append(t_res)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Key Results Analysis:", h2_style))
    story.append(Paragraph("&bull; <b>High Precision early warnings:</b> The model achieves a Precision of 90.68% and 88.60% at 5m and 15m lead times. When an alert triggers, operators can be highly confident that it is genuine.", bullet_style))
    story.append(Paragraph("&bull; <b>Minimal False Alarm Rate:</b> FAR remains below 0.31% across all horizons, with a minimum of 0.1255% at 5 minutes. This prevents alarm fatigue and builds trust.", bullet_style))
    story.append(Paragraph("&bull; <b>Redundancy Elimination Benefit:</b> By excluding the redundant C3 inlet temp sensor and keeping column bottom temp and C3 pressure, we trained simpler, more robust trees without sacrificing predictive power.", bullet_style))
    
    story.append(PageBreak())
    
    # ============================================================================
    # Section 8: Hyperparameter Optimization & Model Tuning
    # ============================================================================
    story.append(Paragraph("8. Hyperparameter Optimization & Model Tuning", h1_style))
    story.append(Paragraph(
        "To improve prediction accuracy and further reduce false alarms, we performed a hyperparameter optimization "
        "study using <b>Optuna</b>. We optimized LightGBM hyperparameter distributions, including learning rate, "
        "number of leaves, max depth, sample splitting constraints, and regularization. We downsampled the training "
        "and validation sets by taking every 8th record to ensure search speed, running 15 trials per horizon. "
        "The tuned models were then retrained on the full Train dataset and evaluated against the first-cut baseline models "
        "on the held-out late-2025 Test Set.",
        body_style
    ))
    
    t_comp = build_report_table("tuning_comparison_summary.csv", max_rows=9, custom_col_widths=[60, 100, 50, 50, 50, 60, 60, 60])
    if t_comp: story.append(t_comp)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Tuning Performance Insights:", h2_style))
    story.append(Paragraph("&bull; <b>Precision and F1-Score Improvements:</b> The tuned models demonstrate consistent increases in Precision across all horizons (e.g., 5m Precision increased from 90.68% to 91.01%; 15m from 88.60% to 89.08%). This raises operator confidence in alarm validity.", bullet_style))
    story.append(Paragraph("&bull; <b>Further Reduced False Alarms:</b> The False Alarm Rate (FAR) is systematically reduced (e.g., 5m FAR dropped from 0.1255% to 0.1204%), which directly supports control room operator trust and prevents alarm fatigue.", bullet_style))
    story.append(Paragraph("&bull; <b>Feature Importance Consistency:</b> Extracting split importances from the tuned models (using the newly generated tuned_feature_importance.csv) confirms that ambient/diurnal indicators ('hour' and 'month') rank highest, followed by separator pressure changes (03PIC_1023.PV_diff_5) and cooling loop temperature feedback (03TI_1081.PV_diff_5). This reinforces the thermodynamic process drivers identified during EDA.", bullet_style))
    
    story.append(PageBreak())
    
    # ============================================================================
    # Section 9: Actionable Recommendations
    # ============================================================================
    story.append(Paragraph("9. Actionable Recommendations", h1_style))
    story.append(Paragraph(
        "Based on the advanced diagnostic analysis and modeling results, we propose the following actionable steps "
        "for modeling and plant operations:",
        body_style
    ))
    
    story.append(Paragraph("Modeling Guidelines", h2_style))
    story.append(Paragraph("&bull; <b>Feature Selection Priority:</b> Keep the 5-variable key sensor set for lag and rolling calculations. Avoid adding redundant sensors to prevent dimensionality bloat.", bullet_style))
    story.append(Paragraph("&bull; <b>Capped Forward-Fill:</b> Keep the 5-minute capped forward-fill for all data preprocessing. Extending the cap beyond 5 minutes risks leaking synthetic data across shutdown periods, warping model statistics.", bullet_style))
    story.append(Paragraph("&bull; <b>Chattering Suppression:</b> Do not train models on sub-minute crossings (chattering). Filter out alarm episodes ≤ 1 minute from the evaluation test sets to prevent false positive penalties.", bullet_style))
    story.append(Paragraph("&bull; <b>Multi-Horizon Strategy:</b> Maintain four independent models. The 15m model should trigger critical alarms, while the 60m model provides strategic window alerts.", bullet_style))
    
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Plant Operations & Maintenance Guidelines", h2_style))
    story.append(Paragraph("&bull; <b>Condenser Cleaning Schedule:</b> Schedule overhead condenser decoking and cleaning in May, immediately preceding summer. Ambient cooling efficiency degradation in June-August is the primary driver of column heat accumulation.", bullet_style))
    story.append(Paragraph("&bull; <b>Column Bottom Alarm Lead:</b> Since column bottom temperature (03TI_1024.PV) ramps earlier and faster (+0.0155°C/min) than overhead temp (+0.0132°C/min) preceding alarms, configure control room alarms to flag bottom temperature rate-of-rise as a pre-alarm indicator.", bullet_style))
    story.append(Paragraph("&bull; <b>Emergency Cooling Coordination:</b> Once the column overhead temperature clears the 21.0°C threshold, it takes an average of 42.5 minutes for the column to cool back to normal stable baseline (<20°C). Use this slow decay to coordinate reflux adjustments.", bullet_style))
    
    # Generate the document
    doc.build(story, canvasmaker=NumberedCanvas)
    print("PDF Report compiled successfully.")

if __name__ == "__main__":
    generate_pdf()
