const pptxgen = require("pptxgenjs");
const path = require("path");

let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9'; // 10" x 5.625"
pres.title = "Honeywell Temperature Alarm Prediction Model";
pres.author = "Data Science Team";

// Theme Colors
const COLOR_NAVY = "0A1931";
const COLOR_SLATE = "374151";
const COLOR_TEAL = "0D9488";
const COLOR_LIGHT_GRAY = "F3F4F6";
const COLOR_OFF_WHITE = "F9FAFB";
const COLOR_WHITE = "FFFFFF";
const COLOR_LIGHT_BLUE = "E0F2FE";
const COLOR_MUTED = "9CA3AF";
const COLOR_CORAL = "F96167";

// Helper for shadow options to avoid PptxGenJS in-place mutation corruption
const makeShadow = () => ({
  type: "outer",
  color: "000000",
  blur: 6,
  offset: 2,
  angle: 135,
  opacity: 0.15
});

// Font Configuration
const FONT_HEADER = "Trebuchet MS";
const FONT_BODY = "Calibri";

// ============================================================================
// Slide 1: Title Slide (Dark Background)
// ============================================================================
let s1 = pres.addSlide();
s1.background = { color: COLOR_NAVY };

// Add abstract geometric visuals on the right representing data streams
for (let i = 0; i < 5; i++) {
  s1.addShape(pres.shapes.RECTANGLE, {
    x: 6.5 + i * 0.5,
    y: 1.0 + i * 0.3,
    w: 0.2,
    h: 3.5 - i * 0.5,
    fill: { color: COLOR_TEAL, transparency: 30 + i * 15 },
    line: { style: "none" }
  });
}
s1.addShape(pres.shapes.LINE, {
  x: 5.5, y: 2.8, w: 2.5, h: 0,
  line: { color: COLOR_LIGHT_BLUE, width: 2, dashType: "dash" }
});
s1.addShape(pres.shapes.LINE, {
  x: 5.0, y: 2.0, w: 2.0, h: 0,
  line: { color: COLOR_LIGHT_BLUE, width: 1.5, dashType: "dash" }
});

s1.addText("OPC UA TEMPERATURE\nALARM PREDICTOR", {
  x: 0.8, y: 1.2, w: 5.0, h: 1.6,
  fontFace: FONT_HEADER, fontSize: 32, color: COLOR_WHITE, bold: true, margin: 0
});

s1.addText("Early Warning System for Tag 03TIC_1023.PV", {
  x: 0.8, y: 3.0, w: 5.0, h: 0.4,
  fontFace: FONT_BODY, fontSize: 16, color: COLOR_LIGHT_BLUE, italic: true, margin: 0
});

s1.addText([
  { text: "Prepared by: ", options: { bold: true } },
  { text: "Data Science & Process Analytics Team\n" },
  { text: "Date: ", options: { bold: true } },
  { text: "June 2026" }
], {
  x: 0.8, y: 4.2, w: 4.5, h: 0.6,
  fontFace: FONT_BODY, fontSize: 11, color: COLOR_MUTED, margin: 0
});

// ============================================================================
// Slide 2: Business Problem & Objectives (Light Background)
// ============================================================================
let s2 = pres.addSlide();
s2.background = { color: COLOR_OFF_WHITE };

s2.addText("Business Problem & Objectives", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Column: The Problem Card
s2.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s2.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_NAVY },
  line: { style: "none" }
});

s2.addText("The Cost of Over-Temperature", {
  x: 0.9, y: 1.5, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

s2.addText([
  { text: "Process Trips & Downtime\n", options: { bold: true, fontSize: 14, color: COLOR_NAVY } },
  { text: "Sudden high temperature spikes cross critical safety limits, forcing immediate plant shutdown and costly unplanned downtime.\n\n", options: { fontSize: 11, color: COLOR_SLATE } },
  { text: "Equipment Degradation\n", options: { bold: true, fontSize: 14, color: COLOR_NAVY } },
  { text: "Sustained temperature upsets (>21.0°C) degrade column packing and overhead condensers, increasing maintenance overhead.\n\n", options: { fontSize: 11, color: COLOR_SLATE } },
  { text: "Operator Alarm Fatigue\n", options: { bold: true, fontSize: 14, color: COLOR_NAVY } },
  { text: "Traditional threshold alarms trigger too late and spike too often. Operators need proactive warning to take preventative action.", options: { fontSize: 11, color: COLOR_SLATE } }
], {
  x: 0.9, y: 2.0, w: 3.5, h: 2.9,
  fontFace: FONT_BODY, margin: 0
});

// Right Column: Flowchart Solution
s2.addText("Transitioning from Reactive to Proactive", {
  x: 5.2, y: 1.3, w: 4.2, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

// Flowchart step 1
s2.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.8, w: 4.2, h: 0.8,
  fill: { color: COLOR_LIGHT_GRAY },
  line: { color: COLOR_MUTED, width: 1 }
});
s2.addText("1. Process State Normal\nOverhead temperature is stable (< 21.0°C).", {
  x: 5.4, y: 1.9, w: 3.8, h: 0.6,
  fontFace: FONT_BODY, fontSize: 12, color: COLOR_SLATE, margin: 0
});

s2.addText("▼", { x: 7.2, y: 2.65, w: 0.3, h: 0.3, fontFace: FONT_BODY, fontSize: 14, color: COLOR_TEAL, align: "center" });

// Flowchart step 2 (ML Warning - Accent Card)
s2.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 3.0, w: 4.2, h: 0.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_TEAL, width: 2 },
  shadow: makeShadow()
});
s2.addText("2. ML Predicts Threat (5-60m Horizon)\nCalculates rate of rise; flags impending crossing.", {
  x: 5.4, y: 3.1, w: 3.8, h: 0.6,
  fontFace: FONT_BODY, fontSize: 12, color: COLOR_TEAL, bold: true, margin: 0
});

s2.addText("▼", { x: 7.2, y: 3.85, w: 0.3, h: 0.3, fontFace: FONT_BODY, fontSize: 14, color: COLOR_TEAL, align: "center" });

// Flowchart step 3
s2.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 4.2, w: 4.2, h: 0.8,
  fill: { color: COLOR_NAVY },
  line: { style: "none" }
});
s2.addText("3. Operator Adjusts Reflux & Feed\nCooling is increased. Thermal run-up averted.", {
  x: 5.4, y: 4.3, w: 3.8, h: 0.6,
  fontFace: FONT_BODY, fontSize: 12, color: COLOR_WHITE, margin: 0
});

// ============================================================================
// Slide 3: Data Overview & Sourcing (Light Background)
// ============================================================================
let s3 = pres.addSlide();
s3.background = { color: COLOR_OFF_WHITE };

s3.addText("Data Overview & Sourcing", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Column: Sourcing Card
s3.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s3.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_TEAL },
  line: { style: "none" }
});

s3.addText("Honeywell DCS Historian", {
  x: 0.9, y: 1.6, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

s3.addText([
  { text: "Data Source: ", options: { bold: true, color: COLOR_NAVY } },
  { text: "OPC UA Plant Historian database.\n\n", options: { color: COLOR_SLATE } },
  { text: "Time Span: ", options: { bold: true, color: COLOR_NAVY } },
  { text: "4 continuous years (Jan 2022 to Jan 2026).\n\n", options: { color: COLOR_SLATE } },
  { text: "Data Volume: ", options: { bold: true, color: COLOR_NAVY } },
  { text: "2,019,221 records (minutes).\n\n", options: { color: COLOR_SLATE } },
  { text: "Target Variable: ", options: { bold: true, color: COLOR_NAVY } },
  { text: "03TIC_1023.PV (Overhead Temperature in degC).\n\n", options: { color: COLOR_SLATE } },
  { text: "Input Features: ", options: { bold: true, color: COLOR_NAVY } },
  { text: "19 continuous tags representing pressures, flow rates, and temperatures.", options: { color: COLOR_SLATE } }
], {
  x: 0.9, y: 2.2, w: 3.5, h: 2.6,
  fontFace: FONT_BODY, fontSize: 13, margin: 0
});

// Right Column: Grid tags breakdown
s3.addText("Sensor Tag Breakdown", {
  x: 5.2, y: 1.3, w: 4.2, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

// 2x2 grid representing categories
s3.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.8, w: 1.9, h: 1.4, fill: { color: COLOR_WHITE }, line: { color: COLOR_TEAL, width: 2 }, shadow: makeShadow() });
s3.addText("TARGET TAG\n\n03TIC_1023.PV\nOverhead Temp\n(1 tag)", {
  x: 5.3, y: 1.9, w: 1.7, h: 1.2,
  fontFace: FONT_BODY, fontSize: 11, color: COLOR_TEAL, bold: true, align: "center", margin: 0
});

s3.addShape(pres.shapes.RECTANGLE, { x: 7.4, y: 1.8, w: 1.9, h: 1.4, fill: { color: COLOR_WHITE }, line: { color: COLOR_LIGHT_GRAY, width: 1 }, shadow: makeShadow() });
s3.addText("TEMPERATURES\n\n03TI_1024.PV\n03TI_1015.PV\n(15 tags)", {
  x: 7.5, y: 1.9, w: 1.7, h: 1.2,
  fontFace: FONT_BODY, fontSize: 11, color: COLOR_NAVY, align: "center", margin: 0
});

s3.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 3.5, w: 1.9, h: 1.4, fill: { color: COLOR_WHITE }, line: { color: COLOR_LIGHT_GRAY, width: 1 }, shadow: makeShadow() });
s3.addText("PRESSURES\n\n03PIC_1023.PV\n03PIC_1013.PV\n(3 tags)", {
  x: 5.3, y: 3.6, w: 1.7, h: 1.2,
  fontFace: FONT_BODY, fontSize: 11, color: COLOR_NAVY, align: "center", margin: 0
});

s3.addShape(pres.shapes.RECTANGLE, { x: 7.4, y: 3.5, w: 1.9, h: 1.4, fill: { color: COLOR_WHITE }, line: { color: COLOR_LIGHT_GRAY, width: 1 }, shadow: makeShadow() });
s3.addText("FLOW RATES\n\n02FI_1000.PV\nTrain Feed\n(1 tag)", {
  x: 7.5, y: 3.6, w: 1.7, h: 1.2,
  fontFace: FONT_BODY, fontSize: 11, color: COLOR_NAVY, align: "center", margin: 0
});

// ============================================================================
// Slide 4: EDA – Missing Data & Quality Control (Light Background)
// ============================================================================
let s4 = pres.addSlide();
s4.background = { color: COLOR_OFF_WHITE };

s4.addText("EDA – Missing Data & Quality Control", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

s4.addText("Handling Gaps & Ensuring Data Health", {
  x: 0.6, y: 1.3, w: 4.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

s4.addText([
  { text: "Trip / Shutdown Gaps\n", options: { bold: true, color: COLOR_NAVY, fontSize: 14 } },
  { text: "Cross-referencing the 85 shutdown durations confirmed that trip periods had already been removed from the raw parquet data. Gaps remain in the timeline (largest gap = 18.5 days).\n\n", options: { color: COLOR_SLATE, fontSize: 12 } },
  { text: "Small-Gap Imputation\n", options: { bold: true, color: COLOR_NAVY, fontSize: 14 } },
  { text: "Transient sensor drops of 1-5 minutes were forward-filled. Longer gaps were kept as NaNs to prevent model training on synthetic data.\n\n", options: { color: COLOR_SLATE, fontSize: 12 } },
  { text: "Target Tag Quality\n", options: { bold: true, color: COLOR_NAVY, fontSize: 14 } },
  { text: "The target column 03TIC_1023.PV is highly complete, containing only 4 missing values across the 4-year period.", options: { color: COLOR_SLATE, fontSize: 12 } }
], {
  x: 0.6, y: 1.8, w: 4.3, h: 3.2,
  fontFace: FONT_BODY, margin: 0
});

s4.addText("Data Completeness Summary", {
  x: 5.4, y: 1.3, w: 4.0, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

// Bar 1
s4.addText("Target Tag (03TIC_1023.PV)", { x: 5.4, y: 1.8, w: 4.0, h: 0.3, fontFace: FONT_BODY, fontSize: 12, color: COLOR_NAVY, bold: true, margin: 0 });
s4.addShape(pres.shapes.RECTANGLE, { x: 5.4, y: 2.15, w: 4.0, h: 0.35, fill: { color: COLOR_LIGHT_GRAY }, line: { style: "none" } });
s4.addShape(pres.shapes.RECTANGLE, { x: 5.4, y: 2.15, w: 3.999, h: 0.35, fill: { color: COLOR_TEAL }, line: { style: "none" } });
s4.addText("99.9998% (4 missing rows)", { x: 5.5, y: 2.15, w: 3.8, h: 0.35, fontFace: FONT_BODY, fontSize: 11, color: COLOR_WHITE, bold: true, valign: "middle", margin: 0 });

// Bar 2
s4.addText("Highest-Null Tag (03TI_1002.PV)", { x: 5.4, y: 2.8, w: 4.0, h: 0.3, fontFace: FONT_BODY, fontSize: 12, color: COLOR_NAVY, bold: true, margin: 0 });
s4.addShape(pres.shapes.RECTANGLE, { x: 5.4, y: 3.15, w: 4.0, h: 0.35, fill: { color: COLOR_LIGHT_GRAY }, line: { style: "none" } });
s4.addShape(pres.shapes.RECTANGLE, { x: 5.4, y: 3.15, w: 3.990, h: 0.35, fill: { color: COLOR_TEAL }, line: { style: "none" } });
s4.addText("99.85% (3,041 missing rows)", { x: 5.5, y: 3.15, w: 3.8, h: 0.35, fontFace: FONT_BODY, fontSize: 11, color: COLOR_WHITE, bold: true, valign: "middle", margin: 0 });

// Bar 3
s4.addText("Average Tag Completeness", { x: 5.4, y: 3.8, w: 4.0, h: 0.3, fontFace: FONT_BODY, fontSize: 12, color: COLOR_NAVY, bold: true, margin: 0 });
s4.addShape(pres.shapes.RECTANGLE, { x: 5.4, y: 4.15, w: 4.0, h: 0.35, fill: { color: COLOR_LIGHT_GRAY }, line: { style: "none" } });
s4.addShape(pres.shapes.RECTANGLE, { x: 5.4, y: 4.15, w: 3.996, h: 0.35, fill: { color: COLOR_TEAL }, line: { style: "none" } });
s4.addText("99.96% average across 19 tags", { x: 5.5, y: 4.15, w: 3.8, h: 0.35, fontFace: FONT_BODY, fontSize: 11, color: COLOR_WHITE, bold: true, valign: "middle", margin: 0 });

// ============================================================================
// Slide 4B: Advanced Missingness & Imputation Strategy (NEW)
// ============================================================================
let s4b = pres.addSlide();
s4b.background = { color: COLOR_OFF_WHITE };

s4b.addText("Advanced Missingness & Imputation Strategy", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Column: The Imputation Logic
s4b.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s4b.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_TEAL },
  line: { style: "none" }
});
s4b.addText("Consecutive Null Analysis", {
  x: 0.9, y: 1.6, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});
s4b.addText([
  { text: "Conditional Imputation Rules:\n", options: { bold: true, color: COLOR_NAVY, fontSize: 13 } },
  { text: "• Above 60% total nulls: ", options: { bold: true, color: COLOR_TEAL } },
  { text: "Use MICE (Multivariate Imputation by Chained Equations) to capture multi-variable dependencies.\n", options: { fontSize: 11, color: COLOR_SLATE } },
  { text: "• Below 60% total nulls: ", options: { bold: true, color: COLOR_TEAL } },
  { text: "Use Forward-Fill (limit 5 mins) to propagate the last known state.\n\n", options: { fontSize: 11, color: COLOR_SLATE } },
  { text: "Dataset Application:\n", options: { bold: true, color: COLOR_NAVY, fontSize: 13 } },
  { text: "No columns exceeded the 60% MICE threshold (maximum null rate was 0.15% on 03TI_1002.PV). Thus, a 5-minute forward-fill was applied to all tags, resolving all NaNs safely without synthetic bias.", options: { fontSize: 11, color: COLOR_SLATE } }
], {
  x: 0.9, y: 2.1, w: 3.5, h: 2.8,
  fontFace: FONT_BODY, fontSize: 11, margin: 0
});

// Right Column: Table of Consecutive Nulls
s4b.addText("Top Consecutive Null Episodes", {
  x: 5.2, y: 1.3, w: 4.2, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

s4b.addTable([
  [
    { text: "Sensor Tag", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } },
    { text: "Episodes", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } },
    { text: "Max Gap", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } },
    { text: "Null %", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } },
    { text: "Imputation", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } }
  ],
  ["03TI_1002.PV", "7", "2,224 min", "0.1506%", "Forward-Fill"],
  ["02FI_1000.PV", "228", "86 min", "0.0331%", "Forward-Fill"],
  ["03FIC_1085.PV", "167", "10 min", "0.0156%", "Forward-Fill"],
  ["03PDI_1077.PV", "11", "2 min", "0.0006%", "Forward-Fill"],
  ["Others (15 tags)", "≤11 each", "1 min", "<0.0005%", "Forward-Fill"]
], {
  x: 5.2, y: 1.8, w: 4.2, h: 3.0,
  colW: [1.3, 0.7, 0.7, 0.7, 0.8],
  fontFace: FONT_BODY, fontSize: 9,
  border: { pt: 1, color: COLOR_LIGHT_GRAY },
  fill: { color: COLOR_WHITE }
});


// ============================================================================
// Slide 5: EDA – Feature Distributions (Light Background)
// ============================================================================
let s5 = pres.addSlide();
s5.background = { color: COLOR_OFF_WHITE };

s5.addText("EDA – Feature Distributions", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Card
s5.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s5.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_TEAL },
  line: { style: "none" }
});

s5.addText("Normal Operating Envelope", {
  x: 0.9, y: 1.6, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

s5.addText("Most of the plant's runtime represents stable, steady-state process operations.", {
  x: 0.9, y: 2.1, w: 3.5, h: 0.6,
  fontFace: FONT_BODY, fontSize: 13, color: COLOR_SLATE, margin: 0
});

s5.addText("96.89%", {
  x: 0.9, y: 2.8, w: 3.5, h: 0.8,
  fontFace: FONT_HEADER, fontSize: 54, color: COLOR_TEAL, bold: true, margin: 0
});
s5.addText("of data points lie within normal bounds (16.5°C to 18.5°C).", {
  x: 0.9, y: 3.7, w: 3.5, h: 0.8,
  fontFace: FONT_BODY, fontSize: 13, color: COLOR_SLATE, margin: 0
});

// Right Card
s5.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s5.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_CORAL },
  line: { style: "none" }
});

s5.addText("Alarm & Upset Envelope", {
  x: 5.5, y: 1.6, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

s5.addText("The alarm state represents a heavily skewed tail when the column accumulates heat.", {
  x: 5.5, y: 2.1, w: 3.5, h: 0.6,
  fontFace: FONT_BODY, fontSize: 13, color: COLOR_SLATE, margin: 0
});

s5.addText("3.11%", {
  x: 5.5, y: 2.8, w: 3.5, h: 0.8,
  fontFace: FONT_HEADER, fontSize: 54, color: COLOR_CORAL, bold: true, margin: 0
});
s5.addText("of data points exceed the PVHI threshold of >= 21.0°C (62,837 rows in alarm).", {
  x: 5.5, y: 3.7, w: 3.5, h: 0.8,
  fontFace: FONT_BODY, fontSize: 13, color: COLOR_SLATE, margin: 0
});

// ============================================================================
// Slide 6: EDA – Multi-Method Correlation (Updated)
// ============================================================================
let s6 = pres.addSlide();
s6.background = { color: COLOR_OFF_WHITE };

s6.addText("EDA – Multi-Method Correlation", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Column Card
s6.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s6.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_TEAL },
  line: { style: "none" }
});
s6.addText("Thermodynamic & Non-Linear", {
  x: 0.9, y: 1.5, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 18, color: COLOR_NAVY, bold: true, margin: 0
});
s6.addText([
  { text: "Multi-Method Correlation Approach:\n", options: { bold: true, color: COLOR_NAVY, fontSize: 12 } },
  { text: "We ran Pearson (linear), Spearman (rank/monotonic), and Distance Correlation (non-linear) pre-imputation to establish clean process relationships.\n\n", options: { color: COLOR_SLATE, fontSize: 9.5 } },
  { text: "Key Discrepancies Found:\n", options: { bold: true, color: COLOR_NAVY, fontSize: 12 } },
  { text: "• High gaps (>0.30) between Pearson and Spearman (e.g. 03PDI_1077.PV & 03PIC_1068.PV) suggest strong non-linear interactions.\n", options: { color: COLOR_SLATE, fontSize: 9.5 } },
  { text: "• Distance Correlation confirmed strong statistical dependencies (up to 0.71) that standard linear correlation misses.\n\n", options: { color: COLOR_SLATE, fontSize: 9.5 } },
  { text: "SME Variable Removal Placeholder:\n", options: { bold: true, color: COLOR_NAVY, fontSize: 12 } },
  { text: "Highly correlated pairs (|r| ≥ 0.80) are extracted for Subject Matter Expert (SME) review to decide on variable removal to prevent model collinearity issues.", options: { color: COLOR_SLATE, fontSize: 9.5 } }
], {
  x: 0.9, y: 2.0, w: 3.5, h: 2.9,
  fontFace: FONT_BODY, fontSize: 9.5, margin: 0
});

// Right Column: Table of High Correlation Pairs
s6.addText("Flagged High-Correlation Pairs (|r| ≥ 0.80)", {
  x: 5.2, y: 1.2, w: 4.2, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

s6.addTable([
  [
    { text: "Variable Pair", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } },
    { text: "Pearson r", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } },
    { text: "Spearman ρ", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } },
    { text: "Dist Corr", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } },
    { text: "Type", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } }
  ],
  ["03TI_1015.PV & 03TI_1024.PV", "0.9896", "0.9789", "0.9799", "Inter-Var"],
  ["03TIC_1023.PV & 03TI_1024.PV", "0.9840", "0.9568", "0.9661", "With Target"],
  ["03TIC_1023.PV & 03TI_1015.PV", "0.9804", "0.9537", "0.9628", "With Target"],
  ["03PIC_1023.PV & 03TI_1015.PV", "0.9796", "0.9643", "0.9648", "Inter-Var"],
  ["03PIC_1023.PV & 03TI_1024.PV", "0.9787", "0.9635", "0.9651", "Inter-Var"],
  ["02FI_1000.PV & 03PDI_1020.PV", "0.9759", "0.8515", "0.9635", "Inter-Var"],
  ["03TI_1002.PV & 03TI_1005.PV", "0.9654", "0.9648", "0.9551", "Inter-Var"]
], {
  x: 5.2, y: 1.7, w: 4.2, h: 3.0,
  colW: [1.6, 0.6, 0.8, 0.6, 0.6],
  fontFace: FONT_BODY, fontSize: 8,
  border: { pt: 1, color: COLOR_LIGHT_GRAY },
  fill: { color: COLOR_WHITE }
});

// ============================================================================
// Slide 6B: Alarm Duration & Chattering Analysis (NEW)
// ============================================================================
let s6b = pres.addSlide();
s6b.background = { color: COLOR_OFF_WHITE };

s6b.addText("EDA – Alarm Duration & Chattering Analysis", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Column Card: Duration Buckets
s6b.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s6b.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_NAVY },
  line: { style: "none" }
});
s6b.addText("Alarm Duration Windowing", {
  x: 0.9, y: 1.4, w: 3.5, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 16, color: COLOR_NAVY, bold: true, margin: 0
});
s6b.addText([
  { text: "Alarm Duration Characteristics:\n", options: { bold: true, color: COLOR_NAVY, fontSize: 12 } },
  { text: "We bucketed the 1,561 distinct alarm events to understand process dynamics:\n\n", options: { color: COLOR_SLATE, fontSize: 9.5 } },
  { text: "• 0-1 min (Sensor Noise/Chattering): ", options: { bold: true, color: COLOR_CORAL, fontSize: 9.5 } },
  { text: "304 episodes (19.5% of total events, but only 304 minutes total duration).\n", options: { fontSize: 9.5, color: COLOR_SLATE } },
  { text: "• 1-5 min (Short Spikes): ", options: { bold: true, color: COLOR_TEAL, fontSize: 9.5 } },
  { text: "291 episodes (18.6% of events, 881 mins total).\n", options: { fontSize: 9.5, color: COLOR_SLATE } },
  { text: "• 5-15 min (Moderate Upsets): ", options: { bold: true, color: COLOR_TEAL, fontSize: 9.5 } },
  { text: "240 episodes (15.4% of events, 2,265 mins total).\n", options: { fontSize: 9.5, color: COLOR_SLATE } },
  { text: "• 15-60 min (Significant Upsets): ", options: { bold: true, color: COLOR_NAVY, fontSize: 9.5 } },
  { text: "142 episodes (9.1% of events, 4,023 mins total).\n", options: { fontSize: 9.5, color: COLOR_SLATE } },
  { text: "• 60+ min (Sustained Thermal Events): ", options: { bold: true, color: COLOR_NAVY, fontSize: 9.5 } },
  { text: "214 episodes (13.7% of events, 53,829 mins total). This accounts for 87% of all alarm downtime, driven by major thermal upsets of 8-9 hours.", options: { fontSize: 9.5, color: COLOR_SLATE } }
], {
  x: 0.9, y: 2.1, w: 3.5, h: 2.9,
  fontFace: FONT_BODY, fontSize: 9.5, margin: 0
});

// Right Column Card: Chattering Analysis
s6b.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.2, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s6b.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.2, h: 0.08,
  fill: { color: COLOR_TEAL },
  line: { style: "none" }
});
s6b.addText("Chattering Detection & Noise Isolation", {
  x: 5.5, y: 1.4, w: 3.6, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 16, color: COLOR_NAVY, bold: true, margin: 0
});
s6b.addText([
  { text: "Operational Noise Definition:\n", options: { bold: true, color: COLOR_TEAL, fontSize: 12 } },
  { text: "Chattering is defined as brief alarm crossings (≤1 min) separated by less than 5 minutes of normal operation. These represent control loop noise rather than structural plant upsets.\n\n", options: { color: COLOR_SLATE, fontSize: 10 } },
  { text: "Chattering Summary:\n", options: { bold: true, color: COLOR_TEAL, fontSize: 12 } },
  { text: "• Total Chattering Sequences: ", options: { bold: true, color: COLOR_CORAL, fontSize: 10 } },
  { text: "360 chattering episodes identified.\n", options: { fontSize: 10, color: COLOR_SLATE } },
  { text: "• Total Chattering Time: ", options: { bold: true, color: COLOR_CORAL, fontSize: 10 } },
  { text: "Under 6 hours of cumulative runtime.\n\n", options: { fontSize: 10, color: COLOR_SLATE } },
  { text: "Why This Matters:\n", options: { bold: true, color: COLOR_NAVY, fontSize: 12 } },
  { text: "Isolating chattering prevents alarm fatigue. The machine learning model should be tuned to ignore these sub-minute crossings, focusing its early warning capacity on moderate (5-15m) and sustained (60m+) thermal run-ups.", options: { color: COLOR_SLATE, fontSize: 10 } }
], {
  x: 5.5, y: 2.1, w: 3.6, h: 2.9,
  fontFace: FONT_BODY, fontSize: 10, margin: 0
});

// ============================================================================
// Slide 6C: Pre/Post-Alarm Behavioral Profiles (NEW)
// ============================================================================
let s6c = pres.addSlide();
s6c.background = { color: COLOR_OFF_WHITE };

s6c.addText("EDA – Pre & Post-Alarm System Profiles", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Column Card: Pre-Alarm behavior
s6c.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s6c.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_TEAL },
  line: { style: "none" }
});
s6c.addText("Pre-Alarm System Ramping (30m Lead)", {
  x: 0.9, y: 1.4, w: 3.5, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 16, color: COLOR_NAVY, bold: true, margin: 0
});
s6c.addText([
  { text: "Rate of Change (30 mins before alarm start):\n", options: { bold: true, color: COLOR_NAVY, fontSize: 12 } },
  { text: "By tracking sensor behavior preceding threshold crossings, we identified leading thermodynamic indicators:\n\n", options: { color: COLOR_SLATE, fontSize: 10 } },
  { text: "• Target Overhead Temp (03TIC_1023.PV): ", options: { bold: true, color: COLOR_NAVY, fontSize: 10 } },
  { text: "Ramp rate of +0.0132°C/min, representing an average 30m increase of +0.39°C.\n", options: { fontSize: 10, color: COLOR_SLATE } },
  { text: "• Column Inlet Temp (03TI_1024.PV): ", options: { bold: true, color: COLOR_TEAL, fontSize: 10 } },
  { text: "Ramp rate of +0.0155°C/min, demonstrating that heat rise originates at the column bottom and works upward.\n", options: { fontSize: 10, color: COLOR_SLATE } },
  { text: "• C3 Inlet Temp (03TI_1015.PV): ", options: { bold: true, color: COLOR_TEAL, fontSize: 10 } },
  { text: "Ramp rate of +0.0136°C/min.\n", options: { fontSize: 10, color: COLOR_SLATE } },
  { text: "• C3 Separator Press (03PIC_1023.PV): ", options: { bold: true, color: COLOR_TEAL, fontSize: 10 } },
  { text: "Ramp rate of +0.0021 barg/min.", options: { fontSize: 10, color: COLOR_SLATE } }
], {
  x: 0.9, y: 2.1, w: 3.5, h: 2.9,
  fontFace: FONT_BODY, fontSize: 10, margin: 0
});

// Right Column Card: Recovery Profiles
s6c.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.2, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s6c.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.2, h: 0.08,
  fill: { color: COLOR_NAVY },
  line: { style: "none" }
});
s6c.addText("Post-Alarm Cooldown & Recovery", {
  x: 5.5, y: 1.4, w: 3.6, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 16, color: COLOR_NAVY, bold: true, margin: 0
});
s6c.addText([
  { text: "Post-Alarm Thermal Recovery:\n", options: { bold: true, color: COLOR_TEAL, fontSize: 12 } },
  { text: "How quickly does the system recover once the cooling utilities respond?\n\n", options: { color: COLOR_SLATE, fontSize: 10 } },
  { text: "• Cooldown Rates: ", options: { bold: true, color: COLOR_TEAL, fontSize: 10 } },
  { text: "Average cooldown rate is -0.0125°C/min, slightly slower than the run-up rate due to physical thermal inertia in the condenser tubes.\n\n", options: { fontSize: 10, color: COLOR_SLATE } },
  { text: "• Recovery Time: ", options: { bold: true, color: COLOR_TEAL, fontSize: 10 } },
  { text: "Once the alarm threshold is cleared (overhead temperature falls below 21.0°C), it takes an average of 42.5 minutes for the column to return to its stable baseline operating zone (< 20.0°C).\n\n", options: { fontSize: 10, color: COLOR_SLATE } },
  { text: "Why This Matters:\n", options: { bold: true, color: COLOR_NAVY, fontSize: 12 } },
  { text: "This slow thermal decay confirms that predicting alarm end/recovery is as critical for plant coordination as predicting alarm onset.", options: { color: COLOR_SLATE, fontSize: 10 } }
], {
  x: 5.5, y: 2.1, w: 3.6, h: 2.9,
  fontFace: FONT_BODY, fontSize: 10, margin: 0
});

// ============================================================================
// Slide 6D: Post-Trip Verification & Split Balance (NEW)
// ============================================================================
let s6d = pres.addSlide();
s6d.background = { color: COLOR_OFF_WHITE };

s6d.addText("EDA – Post-Trip Verification & Split Balance", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Column Card: Post-Trip False Alarms
s6d.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s6d.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_CORAL },
  line: { style: "none" }
});
s6d.addText("Post-Trip False Alarm Check", {
  x: 0.9, y: 1.4, w: 3.5, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 16, color: COLOR_NAVY, bold: true, margin: 0
});
s6d.addText([
  { text: "Cross-referencing 85 plant trip end times:\n", options: { bold: true, color: COLOR_NAVY, fontSize: 12 } },
  { text: "We checked if residual thermal signatures after restarts trigger false alarms in different windows:\n\n", options: { color: COLOR_SLATE, fontSize: 9.5 } },
  { text: "• 10-Minute Window: ", options: { bold: true, color: COLOR_CORAL, fontSize: 9.5 } },
  { text: "2 episodes start within 10 mins of trip end.\n", options: { fontSize: 9.5, color: COLOR_SLATE } },
  { text: "• 20-Minute Window: ", options: { bold: true, color: COLOR_CORAL, fontSize: 9.5 } },
  { text: "2 episodes start within 20 mins.\n", options: { fontSize: 9.5, color: COLOR_SLATE } },
  { text: "• 60-Minute Window: ", options: { bold: true, color: COLOR_CORAL, fontSize: 9.5 } },
  { text: "10 episodes start within 60 mins.\n", options: { fontSize: 9.5, color: COLOR_SLATE } },
  { text: "• 120-Minute Window: ", options: { bold: true, color: COLOR_CORAL, fontSize: 9.5 } },
  { text: "12 episodes start within 120 mins.\n\n", options: { fontSize: 9.5, color: COLOR_SLATE } },
  { text: "Operational Significance:\n", options: { bold: true, color: COLOR_NAVY, fontSize: 12 } },
  { text: "Out of 1,561 alarms, only 12 (0.7%) occurred immediately after trips, confirming that post-trip thermal residuals are not a significant source of false alarms in this dataset.", options: { fontSize: 9.5, color: COLOR_SLATE } }
], {
  x: 0.9, y: 2.1, w: 3.5, h: 2.9,
  fontFace: FONT_BODY, fontSize: 9.5, margin: 0
});

// Right Column Card: Split Balance
s6d.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.2, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s6d.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.2, h: 0.08,
  fill: { color: COLOR_TEAL },
  line: { style: "none" }
});
s6d.addText("Evaluating Data Split Balance", {
  x: 5.5, y: 1.4, w: 3.6, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 16, color: COLOR_NAVY, bold: true, margin: 0
});
s6d.addText([
  { text: "Train / Val / Test Alarm Consistency:\n", options: { bold: true, color: COLOR_TEAL, fontSize: 12 } },
  { text: "To verify evaluation reliability, we analyzed alarm representation across the chronological partitions:\n\n", options: { color: COLOR_SLATE, fontSize: 9.5 } },
  { text: "• Train Split (2022-2024):\n", options: { bold: true, color: COLOR_NAVY, fontSize: 9.5 } },
  { text: "1,088 distinct episodes, alarm rate of 3.16% (average duration: 44.7m).\n", options: { fontSize: 9.5, color: COLOR_SLATE } },
  { text: "• Val Split (H1 2025):\n", options: { bold: true, color: COLOR_NAVY, fontSize: 9.5 } },
  { text: "155 distinct episodes, alarm rate of 1.85% (average duration: 30.1m).\n", options: { fontSize: 9.5, color: COLOR_SLATE } },
  { text: "• Test Split (H2 2025+):\n", options: { bold: true, color: COLOR_NAVY, fontSize: 9.5 } },
  { text: "318 distinct episodes, alarm rate of 2.99% (average duration: 25.1m).\n\n", options: { fontSize: 9.5, color: COLOR_SLATE } },
  { text: "Why This Matters:\n", options: { bold: true, color: COLOR_NAVY, fontSize: 12 } },
  { text: "The alarm rates and sample sizes are well-balanced across all splits, ensuring that offline evaluation is highly representative.", options: { color: COLOR_SLATE, fontSize: 9.5 } }
], {
  x: 5.5, y: 2.1, w: 3.6, h: 2.9,
  fontFace: FONT_BODY, fontSize: 9.5, margin: 0
});


// ============================================================================
// Slide 7: Why Feature Engineering is Needed (NEW)
// ============================================================================
let s7 = pres.addSlide();
s7.background = { color: COLOR_OFF_WHITE };

s7.addText("Why Feature Engineering is Needed", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Card: The Snapshot Limit
s7.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s7.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_CORAL },
  line: { style: "none" }
});
s7.addText("The Limit of Raw Snapshots", {
  x: 0.9, y: 1.6, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});
s7.addText([
  { text: "Static readings at instant t contain no momentum.\n\n", options: { bold: true, fontSize: 13, color: COLOR_NAVY } },
  { text: "If the current temperature is 20.5°C:\n", options: { fontSize: 12, color: COLOR_SLATE } },
  { text: "• Case A: ", options: { bold: true, color: COLOR_TEAL } },
  { text: "It was 21.0°C ten minutes ago and is falling. The system is cooling down. ", options: { fontSize: 11, color: COLOR_SLATE } },
  { text: "No alarm threat.\n", options: { bold: true, color: COLOR_TEAL } },
  { text: "• Case B: ", options: { bold: true, color: COLOR_CORAL } },
  { text: "It was 19.0°C ten minutes ago and is rising rapidly. The system is overheating. ", options: { fontSize: 11, color: COLOR_SLATE } },
  { text: "Critical alarm threat.\n\n", options: { bold: true, color: COLOR_CORAL } },
  { text: "A snapshot model sees 20.5°C in both cases and makes the same prediction. It cannot distinguish between cooling and heating.", options: { fontSize: 11, color: COLOR_SLATE } }
], {
  x: 0.9, y: 2.1, w: 3.5, h: 2.8,
  fontFace: FONT_BODY, margin: 0
});

// Right Card: How Feature Engineering Improves Predictiveness
s7.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s7.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_TEAL },
  line: { style: "none" }
});
s7.addText("How Context Improves Predictiveness", {
  x: 5.5, y: 1.6, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});
s7.addText([
  { text: "By adding history, velocity, and variance, we allow the model to:\n\n", options: { fontSize: 12, color: COLOR_SLATE } },
  { text: "1. Detect Trends Early\n", options: { bold: true, fontSize: 13, color: COLOR_NAVY } },
  { text: "Know if values are compounding or decaying over time.\n\n", options: { fontSize: 11, color: COLOR_SLATE } },
  { text: "2. Capture Rate of Rise\n", options: { bold: true, fontSize: 13, color: COLOR_NAVY } },
  { text: "Calculate the exact speed of temperature changes to anticipate threshold crossings.\n\n", options: { fontSize: 11, color: COLOR_SLATE } },
  { text: "3. Identify Instability\n", options: { bold: true, fontSize: 13, color: COLOR_NAVY } },
  { text: "Measure sensor oscillations (volatility) which physically precede columns flooding or tripping.", options: { fontSize: 11, color: COLOR_SLATE } }
], {
  x: 5.5, y: 2.1, w: 3.5, h: 2.8,
  fontFace: FONT_BODY, margin: 0
});

// ============================================================================
// Slide 8: The Feature Library - Lags & Rolling Averages (NEW)
// ============================================================================
let s8 = pres.addSlide();
s8.background = { color: COLOR_OFF_WHITE };

s8.addText("The Feature Library – Lags & Rolling Averages", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Column Card: Lags
s8.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s8.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_NAVY },
  line: { style: "none" }
});
s8.addText("Lag Features (History)", {
  x: 0.9, y: 1.6, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});
s8.addText([
  { text: "Definition:\n", options: { bold: true, color: COLOR_TEAL, fontSize: 12 } },
  { text: "The value of a sensor tag shifted backward in time.\n", options: { fontSize: 11, color: COLOR_SLATE } },
  { text: "Calculation:\n", options: { bold: true, color: COLOR_TEAL, fontSize: 12 } },
  { text: "Lag(X, k) = X_t-k  (k = 1, 2, 5, 10, 15, 30, 60 minutes)\n", options: { fontSize: 11, color: COLOR_SLATE, fontFace: "Consolas" } },
  { text: "Operational Value:\n", options: { bold: true, color: COLOR_TEAL, fontSize: 12 } },
  { text: "Provides the model with direct historical snapshots. By comparing current value X_t with X_t-15, the model can infer the direction of the process variable.", options: { fontSize: 11, color: COLOR_SLATE } }
], {
  x: 0.9, y: 2.1, w: 3.5, h: 2.8,
  fontFace: FONT_BODY, margin: 0
});

// Right Column Card: Rolling Means
s8.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s8.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_NAVY },
  line: { style: "none" }
});
s8.addText("Rolling Averages (Baselines)", {
  x: 5.5, y: 1.6, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});
s8.addText([
  { text: "Definition:\n", options: { bold: true, color: COLOR_TEAL, fontSize: 12 } },
  { text: "The average value of a sensor over a sliding time window.\n", options: { fontSize: 11, color: COLOR_SLATE } },
  { text: "Calculation:\n", options: { bold: true, color: COLOR_TEAL, fontSize: 12 } },
  { text: "Mean(X, w) = (1/w) * Sum(X_t-i) from i=0 to w-1  (w = 10, 30, 60 mins)\n", options: { fontSize: 11, color: COLOR_SLATE, fontFace: "Consolas" } },
  { text: "Operational Value:\n", options: { bold: true, color: COLOR_TEAL, fontSize: 12 } },
  { text: "Filters out high-frequency sensor noise to reveal the operational baseline. If the 60-minute rolling average is climbing, it represents a slow, systemic heat buildup.", options: { fontSize: 11, color: COLOR_SLATE } }
], {
  x: 5.5, y: 2.1, w: 3.5, h: 2.8,
  fontFace: FONT_BODY, margin: 0
});

// ============================================================================
// Slide 9: The Feature Library - Volatility & Velocity (NEW)
// ============================================================================
let s9 = pres.addSlide();
s9.background = { color: COLOR_OFF_WHITE };

s9.addText("The Feature Library – Volatility & Velocity", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Column Card: Volatility (Std Dev)
s9.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s9.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_NAVY },
  line: { style: "none" }
});
s9.addText("Rolling Volatility (Instability)", {
  x: 0.9, y: 1.6, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});
s9.addText([
  { text: "Definition:\n", options: { bold: true, color: COLOR_TEAL, fontSize: 12 } },
  { text: "The standard deviation of a sensor over a sliding time window.\n", options: { fontSize: 11, color: COLOR_SLATE } },
  { text: "Calculation:\n", options: { bold: true, color: COLOR_TEAL, fontSize: 12 } },
  { text: "Std(X, w) = Sqrt( (1/w) * Sum( (X_t-i - Mean)^2 ) )  (w = 10, 30, 60 mins)\n", options: { fontSize: 11, color: COLOR_SLATE, fontFace: "Consolas" } },
  { text: "Operational Value:\n", options: { bold: true, color: COLOR_TEAL, fontSize: 12 } },
  { text: "Measures process instability. Rapid pressure or flow oscillations indicate column flooding or unstable control loops, which often occur immediately before thermal upsets.", options: { fontSize: 11, color: COLOR_SLATE } }
], {
  x: 0.9, y: 2.1, w: 3.5, h: 2.8,
  fontFace: FONT_BODY, margin: 0
});

// Right Column Card: Velocity (Differences)
s9.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s9.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_NAVY },
  line: { style: "none" }
});
s9.addText("Differences (Rate of Change)", {
  x: 5.5, y: 1.6, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});
s9.addText([
  { text: "Definition:\n", options: { bold: true, color: COLOR_TEAL, fontSize: 12 } },
  { text: "The difference between current value and historical value (derivative).\n", options: { fontSize: 11, color: COLOR_SLATE } },
  { text: "Calculation:\n", options: { bold: true, color: COLOR_TEAL, fontSize: 12 } },
  { text: "Diff(X, d) = X_t - X_t-d  (d = 5, 15, 30 minutes)\n", options: { fontSize: 11, color: COLOR_SLATE, fontFace: "Consolas" } },
  { text: "Operational Value:\n", options: { bold: true, color: COLOR_TEAL, fontSize: 12 } },
  { text: "Measures the rate of thermal change (velocity). A large positive difference shows a rapid heat build-up. This helps the model anticipate threshold crossings long before they occur.", options: { fontSize: 11, color: COLOR_SLATE } }
], {
  x: 5.5, y: 2.1, w: 3.5, h: 2.8,
  fontFace: FONT_BODY, margin: 0
});

// ============================================================================
// Slide 10: Feature Engineering & Preprocessing (Light Background)
// ============================================================================
let s10 = pres.addSlide();
s10.background = { color: COLOR_OFF_WHITE };

s10.addText("Feature Engineering & Preprocessing", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

const stepWidth = 2.0;
const stepGap = 0.2;
const startX = 0.6;
const stepY = 1.6;

const stepData = [
  { num: "1", title: "Time-Alignment", desc: "Reindexed to a regular 1-minute grid. Shutdown periods placed as NaNs to prevent false cross-gap rolling window averages." },
  { num: "2", title: "Feature Construction", desc: "Created 132 features: lags (1-60m), rolling mean/std/min/max (10, 30, 60m), and rates of change (5, 15, 30m diffs)." },
  { num: "3", title: "Target Offsets", desc: "Shifted target column by -15m, -30m, and -60m to align model input features with the future forecast horizons." },
  { num: "4", title: "Chronological Split", desc: "Divided data: Train (22-24), Val (H1 25), Test (H2 25). Prevents time-series data leakage and secures model reliability." }
];

for (let i = 0; i < 4; i++) {
  let xPos = startX + i * (stepWidth + stepGap);
  
  s10.addShape(pres.shapes.RECTANGLE, {
    x: xPos, y: stepY, w: stepWidth, h: 3.3,
    fill: { color: COLOR_WHITE },
    line: { color: COLOR_LIGHT_GRAY, width: 1 },
    shadow: makeShadow()
  });
  
  s10.addShape(pres.shapes.OVAL, {
    x: xPos + 0.8, y: stepY + 0.2, w: 0.4, h: 0.4,
    fill: { color: COLOR_TEAL },
    line: { style: "none" }
  });
  s10.addText(stepData[i].num, {
    x: xPos + 0.8, y: stepY + 0.2, w: 0.4, h: 0.4,
    fontFace: FONT_HEADER, fontSize: 14, color: COLOR_WHITE, bold: true, align: "center", valign: "middle", margin: 0
  });
  
  s10.addText(stepData[i].title, {
    x: xPos + 0.1, y: stepY + 0.8, w: stepWidth - 0.2, h: 0.4,
    fontFace: FONT_HEADER, fontSize: 14, color: COLOR_NAVY, bold: true, align: "center", margin: 0
  });
  
  s10.addText(stepData[i].desc, {
    x: xPos + 0.1, y: stepY + 1.3, w: stepWidth - 0.2, h: 1.8,
    fontFace: FONT_BODY, fontSize: 11, color: COLOR_SLATE, align: "left", margin: 0
  });
  
  if (i < 3) {
    s10.addText("►", {
      x: xPos + stepWidth, y: stepY + 1.4, w: stepGap, h: 0.4,
      fontFace: FONT_BODY, fontSize: 16, color: COLOR_TEAL, align: "center", valign: "middle"
    });
  }
}

// ============================================================================
// Slide 10A: Step 1 - Time-Alignment & Quality Control (Light Background)
// ============================================================================
let s10a = pres.addSlide();
s10a.background = { color: COLOR_OFF_WHITE };

s10a.addText("Step 1 – Time-Alignment & Quality Control", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Column: The Problem and Solution
s10a.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s10a.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_TEAL },
  line: { style: "none" }
});

s10a.addText("Aligning Chronological Gaps", {
  x: 0.9, y: 1.5, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

s10a.addText([
  { text: "The Challenge of Shutdown Gaps\n", options: { bold: true, color: COLOR_NAVY, fontSize: 13 } },
  { text: "Industrial columns experience shutdowns. Removing trip periods results in timestamp jumps. Calculating rolling statistics across these jumps leads to 'temporal teleportation', combining data weeks apart as if they were adjacent minutes.\n\n", options: { color: COLOR_SLATE, fontSize: 11 } },
  { text: "The Regular Grid Solution\n", options: { bold: true, color: COLOR_NAVY, fontSize: 13 } },
  { text: "Reindexed the data to a strict 1-minute grid, filling missing minutes as NaNs. Forward-filling (ffill) is strictly capped at 5 minutes for transient sensor drops, preventing synthetic data leakage during major shutdowns.", options: { color: COLOR_SLATE, fontSize: 11 } }
], {
  x: 0.9, y: 2.0, w: 3.5, h: 2.9,
  fontFace: FONT_BODY, margin: 0
});

// Right Column: Quality Metrics Card
s10a.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.2, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_TEAL, width: 2 },
  shadow: makeShadow()
});
s10a.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.2, h: 0.08,
  fill: { color: COLOR_NAVY },
  line: { style: "none" }
});

s10a.addText("Process Quality Control Rules", {
  x: 5.5, y: 1.5, w: 3.6, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

s10a.addText([
  { text: "Data Completeness\n", options: { bold: true, color: COLOR_TEAL, fontSize: 13 } },
  { text: "Average tag completeness is 99.96%. Shutdown periods are successfully isolated as NaN rows. Rolling features ignore these values or handle them strictly, ensuring model integrity.\n\n", options: { color: COLOR_SLATE, fontSize: 11 } },
  { text: "Rolling Window Integrity\n", options: { bold: true, color: COLOR_TEAL, fontSize: 13 } },
  { text: "Because the index is strictly regular, a rolling window of 60 is guaranteed to represent exactly 60 minutes of elapsed time, avoiding data misalignment.", options: { color: COLOR_SLATE, fontSize: 11 } }
], {
  x: 5.5, y: 2.0, w: 3.6, h: 2.9,
  fontFace: FONT_BODY, margin: 0
});


// ============================================================================
// Slide 10B: Step 2 - Feature Construction Library (Light Background)
// ============================================================================
let s10b = pres.addSlide();
s10b.background = { color: COLOR_OFF_WHITE };

s10b.addText("Step 2 – Feature Construction Library", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Column: Process Context Card
s10b.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s10b.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_TEAL },
  line: { style: "none" }
});

s10b.addText("132 Engineered Features", {
  x: 0.9, y: 1.5, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

s10b.addText([
  { text: "Lags (Time Context)\n", options: { bold: true, color: COLOR_NAVY, fontSize: 13 } },
  { text: "Captures value momentum. Shifting sensors backward by 1m, 2m, 5m, 10m, 15m, 30m, and 60m lets the model see current values relative to the past.\n\n", options: { color: COLOR_SLATE, fontSize: 11 } },
  { text: "Rolling Statistics\n", options: { bold: true, color: COLOR_NAVY, fontSize: 13 } },
  { text: "Standard deviations over 10m, 30m, and 60m identify process volatility. Means smooth out sensor noise to show slow systemic drift.\n\n", options: { color: COLOR_SLATE, fontSize: 11 } },
  { text: "Differences (Velocity)\n", options: { bold: true, color: COLOR_NAVY, fontSize: 13 } },
  { text: "Computes mathematical derivatives (rate of change) over 5m, 15m, and 30m intervals.", options: { color: COLOR_SLATE, fontSize: 11 } }
], {
  x: 0.9, y: 2.0, w: 3.5, h: 2.9,
  fontFace: FONT_BODY, margin: 0
});

// Right Column: Handling Correlations Card
s10b.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.2, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_TEAL, width: 2 },
  shadow: makeShadow()
});
s10b.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.2, h: 0.08,
  fill: { color: COLOR_NAVY },
  line: { style: "none" }
});

s10b.addText("Tree Ensemble Strengths", {
  x: 5.5, y: 1.5, w: 3.6, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

s10b.addText([
  { text: "Handling Multicollinearity\n", options: { bold: true, color: COLOR_TEAL, fontSize: 13 } },
  { text: "Decision trees handle highly correlated (collinear) sensors naturally. Instead of failing like linear models, LightGBM chooses the best splitting variable, allowing us to include overlapping features safely.\n\n", options: { color: COLOR_SLATE, fontSize: 11 } },
  { text: "Non-Linear Relationships\n", options: { bold: true, color: COLOR_TEAL, fontSize: 13 } },
  { text: "Process variables interact non-linearly. Tree architectures capture these physical thresholds without complex structural assumptions.", options: { color: COLOR_SLATE, fontSize: 11 } }
], {
  x: 5.5, y: 2.0, w: 3.6, h: 2.9,
  fontFace: FONT_BODY, margin: 0
});


// ============================================================================
// Slide 10C: Step 3 - Multi-Horizon Target Offsets (Light Background)
// ============================================================================
let s10c = pres.addSlide();
s10c.background = { color: COLOR_OFF_WHITE };

s10c.addText("Step 3 – Multi-Horizon Target Offsets", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Column: Target Shifts
s10c.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s10c.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_TEAL },
  line: { style: "none" }
});

s10c.addText("Aligning Features with the Future", {
  x: 0.9, y: 1.5, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

s10c.addText([
  { text: "Target Offsets\n", options: { bold: true, color: COLOR_NAVY, fontSize: 13 } },
  { text: "We shift the target column (overhead temperature) backward by -5m, -15m, -30m, and -60m to align the feature vector at time t with the future temperature values at t+k.\n\n", options: { color: COLOR_SLATE, fontSize: 11 } },
  { text: "Why Four Independent Models?\n", options: { bold: true, color: COLOR_NAVY, fontSize: 13 } },
  { text: "The physical predictors evolve at different rates. The 5-minute model relies heavily on recent temperature changes, whereas the 60-minute model must extract features from longer-term pressure and feed trends. Training separate models ensures maximum accuracy at each lead time.", options: { color: COLOR_SLATE, fontSize: 11 } }
], {
  x: 0.9, y: 2.0, w: 3.5, h: 2.9,
  fontFace: FONT_BODY, margin: 0
});

// Right Column: Operational Strategy Card
s10c.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.2, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_TEAL, width: 2 },
  shadow: makeShadow()
});
s10c.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.2, h: 0.08,
  fill: { color: COLOR_NAVY },
  line: { style: "none" }
});

s10c.addText("Multi-Horizon Actions", {
  x: 5.5, y: 1.5, w: 3.6, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

s10c.addText([
  { text: "Alarm Prediction Horizons\n", options: { bold: true, color: COLOR_TEAL, fontSize: 13 } },
  { text: "• 60 Min (Strategic Warning): Gives a long-term forecast allowing operators to adjust suction pressure or coordinate upstream units.\n", options: { color: COLOR_SLATE, fontSize: 11 } },
  { text: "• 30 Min (Tactical Warning): High-probability alert used to prepare bypass valves or adjust utility flows.\n", options: { color: COLOR_SLATE, fontSize: 11 } },
  { text: "• 15 Min (Critical Warning): Emergency warning with a 93% accuracy rate to activate shutdown prevention.\n", options: { color: COLOR_SLATE, fontSize: 11 } },
  { text: "• 5 Min (Emergency Warning): Real-time emergency trigger for immediate manual safety cooling activation and reactor trip signal checks.", options: { color: COLOR_SLATE, fontSize: 11 } }
], {
  x: 5.5, y: 2.0, w: 3.6, h: 2.9,
  fontFace: FONT_BODY, margin: 0
});


// ============================================================================
// Slide 10D: Step 4 - Chronological Split (Light Background)
// ============================================================================
let s10d = pres.addSlide();
s10d.background = { color: COLOR_OFF_WHITE };

s10d.addText("Step 4 – Chronological Splitting", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Column: Splits and Data Leakage
s10d.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s10d.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_TEAL },
  line: { style: "none" }
});

s10d.addText("Securing Model Reliability", {
  x: 0.9, y: 1.5, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

s10d.addText([
  { text: "Timeline Splits\n", options: { bold: true, color: COLOR_NAVY, fontSize: 13 } },
  { text: "We divided our dataset chronologically:\n• Train: Jan 2022 - Dec 2024\n• Val: Jan 2025 - June 2025\n• Test: July 2025 - Jan 2026\n\n", options: { color: COLOR_SLATE, fontSize: 11 } },
  { text: "Why Random Cross-Validation Fails\n", options: { bold: true, color: COLOR_NAVY, fontSize: 13 } },
  { text: "Standard k-fold cross-validation randomly shuffles rows. This leaks future data (the target temperature at t+k) into the training folds, artificially inflating training scores while causing real-world models to fail. Chronological splits keep the training partition strictly in the past.", options: { color: COLOR_SLATE, fontSize: 11 } }
], {
  x: 0.9, y: 2.0, w: 3.5, h: 2.9,
  fontFace: FONT_BODY, margin: 0
});

// Right Column: Operational Validation Card
s10d.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.2, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_TEAL, width: 2 },
  shadow: makeShadow()
});
s10d.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.3, w: 4.2, h: 0.08,
  fill: { color: COLOR_NAVY },
  line: { style: "none" }
});

s10d.addText("Real-World Operational Testing", {
  x: 5.5, y: 1.5, w: 3.6, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

s10d.addText([
  { text: "Simulating Live Performance\n", options: { bold: true, color: COLOR_TEAL, fontSize: 13 } },
  { text: "Evaluating on a continuous, untouched out-of-sample test set (H2 2025) simulates how the models will behave in a live plant, ensuring reliability.\n\n", options: { color: COLOR_SLATE, fontSize: 11 } },
  { text: "Validation and Early Stopping\n", options: { bold: true, color: COLOR_TEAL, fontSize: 13 } },
  { text: "We used the Val partition to stop tree growth when validation RMSE ceased improving, securing the model against overfitting.", options: { color: COLOR_SLATE, fontSize: 11 } }
], {
  x: 5.5, y: 2.0, w: 3.6, h: 2.9,
  fontFace: FONT_BODY, margin: 0
});

// ============================================================================
// Slide 10E: Monthly & Seasonal Alarm Trends (NEW)
// ============================================================================
let s10e = pres.addSlide();
s10e.background = { color: COLOR_OFF_WHITE };

s10e.addText("EDA – Monthly & Seasonal Alarm Trends", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Column Card: Trends Overview
s10e.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s10e.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_TEAL },
  line: { style: "none" }
});
s10e.addText("Seasonal Ambient Influence", {
  x: 0.9, y: 1.4, w: 3.5, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 16, color: COLOR_NAVY, bold: true, margin: 0
});
s10e.addText([
  { text: "Yearly Alarm Frequency:\n", options: { bold: true, color: COLOR_NAVY, fontSize: 12 } },
  { text: "• 2022: 309 episodes | 20,162 total mins (Avg: 65.3m)\n", options: { fontSize: 9.5, color: COLOR_SLATE } },
  { text: "• 2023: 402 episodes | 9,742 total mins (Avg: 24.2m)\n", options: { fontSize: 9.5, color: COLOR_SLATE } },
  { text: "• 2024: 377 episodes | 18,749 total mins (Avg: 49.7m)\n", options: { fontSize: 9.5, color: COLOR_SLATE } },
  { text: "• 2025: 467 episodes | 12,638 total mins (Avg: 27.1m)\n\n", options: { fontSize: 9.5, color: COLOR_SLATE } },
  { text: "Summer vs. Winter Profiles:\n", options: { bold: true, color: COLOR_NAVY, fontSize: 12 } },
  { text: "Alarms peak dramatically during hot summer months (June, July, August) where the ambient air temperature degrades the heat exchange efficiency of the overhead cooling condensers.\n\n", options: { color: COLOR_SLATE, fontSize: 9.5 } },
  { text: "Operational Action:\n", options: { bold: true, color: COLOR_NAVY, fontSize: 12 } },
  { text: "Condenser cleaning and utility cooling flow increases should be scheduled immediately prior to peak summer (May) to maximize column thermal headroom.", options: { color: COLOR_SLATE, fontSize: 9.5 } }
], {
  x: 0.9, y: 2.1, w: 3.5, h: 2.9,
  fontFace: FONT_BODY, fontSize: 9.5, margin: 0
});

// Right Column Card: Seasonal stats table
s10e.addText("Yearly Alarm Accumulation Details", {
  x: 5.2, y: 1.3, w: 4.2, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

s10e.addTable([
  [
    { text: "Year", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } },
    { text: "Episodes", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } },
    { text: "Total Duration", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } },
    { text: "Avg Duration", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } },
    { text: "Max Duration", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } }
  ],
  ["2022", "309", "20,162 min", "65.3 min", "508 min"],
  ["2023", "402", "9,742 min", "24.2 min", "353 min"],
  ["2024", "377", "18,749 min", "49.7 min", "535 min"],
  ["2025", "467", "12,638 min", "27.1 min", "561 min"],
  ["2026 (Jan)", "6", "11 min", "1.8 min", "4 min"]
], {
  x: 5.2, y: 1.8, w: 4.2, h: 3.0,
  colW: [0.8, 0.7, 0.9, 0.9, 0.9],
  fontFace: FONT_BODY, fontSize: 9,
  border: { pt: 1, color: COLOR_LIGHT_GRAY },
  fill: { color: COLOR_WHITE }
});


// ============================================================================
// Slide 11: Model Selection & Training (Light Background)
// ============================================================================
let s11 = pres.addSlide();
s11.background = { color: COLOR_OFF_WHITE };

s11.addText("Model Selection & Training", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

const cWidth = 2.6;
const cGap = 0.4;
const cStartX = 0.6;
const cY = 1.3;

const algos = [
  { name: "Linear Regression", isSelected: false, desc: "A simple linear baseline model.", pros: "Extremely fast, easy to deploy.", cons: "Cannot capture the column's complex thermodynamic non-linear interactions.", choice: "REJECTED (Low Accuracy)" },
  { name: "Deep Learning (LSTM)", isSelected: false, desc: "Recurrent neural network for sequences.", pros: "Excellent sequence memory.", cons: "Huge computational overhead, sensitive to missing value gaps, hard to explain.", choice: "REJECTED (High Complexity)" },
  { name: "LightGBM Regressor", isSelected: true, desc: "Gradient Boosted Decision Tree ensemble.", pros: "Handles non-linear relationships, collinear inputs, native NaNs, ultra-fast training.", cons: "Requires careful hyperparameter tuning.", choice: "SELECTED MODEL" }
];

for (let i = 0; i < 3; i++) {
  let xPos = cStartX + i * (cWidth + cGap);
  let isSel = algos[i].isSelected;
  
  s11.addShape(pres.shapes.RECTANGLE, {
    x: xPos, y: cY, w: cWidth, h: 3.8,
    fill: { color: COLOR_WHITE },
    line: { color: isSel ? COLOR_TEAL : COLOR_LIGHT_GRAY, width: isSel ? 3 : 1 },
    shadow: makeShadow()
  });
  
  s11.addShape(pres.shapes.RECTANGLE, {
    x: xPos, y: cY, w: cWidth, h: 0.08,
    fill: { color: isSel ? COLOR_TEAL : COLOR_NAVY },
    line: { style: "none" }
  });
  
  s11.addText(algos[i].name, {
    x: xPos + 0.15, y: cY + 0.2, w: cWidth - 0.3, h: 0.4,
    fontFace: FONT_HEADER, fontSize: 16, color: isSel ? COLOR_TEAL : COLOR_NAVY, bold: true, align: "center", margin: 0
  });
  
  s11.addText([
    { text: "Description\n", options: { bold: true, fontSize: 12, color: COLOR_NAVY } },
    { text: algos[i].desc + "\n\n", options: { fontSize: 11, color: COLOR_SLATE } },
    { text: "Pros: ", options: { bold: true, fontSize: 11, color: COLOR_TEAL } },
    { text: algos[i].pros + "\n\n", options: { fontSize: 11, color: COLOR_SLATE } },
    { text: "Cons: ", options: { bold: true, fontSize: 11, color: COLOR_CORAL } },
    { text: algos[i].cons, options: { fontSize: 11, color: COLOR_SLATE } }
  ], {
    x: xPos + 0.15, y: cY + 0.8, w: cWidth - 0.3, h: 2.2,
    fontFace: FONT_BODY, margin: 0
  });
  
  s11.addShape(pres.shapes.RECTANGLE, {
    x: xPos + 0.2, y: cY + 3.2, w: cWidth - 0.4, h: 0.4,
    fill: { color: isSel ? COLOR_TEAL : COLOR_LIGHT_GRAY },
    line: { style: "none" }
  });
  s11.addText(algos[i].choice, {
    x: xPos + 0.2, y: cY + 3.2, w: cWidth - 0.4, h: 0.4,
    fontFace: FONT_HEADER, fontSize: 11, color: isSel ? COLOR_WHITE : COLOR_MUTED, bold: true, align: "center", valign: "middle", margin: 0
  });
}

// ============================================================================
// Slide 12: Hyperparameter Tuning via Optuna (Light Background)
// ============================================================================
let s12 = pres.addSlide();
s12.background = { color: COLOR_OFF_WHITE };

s12.addText("Hyperparameter Tuning via Optuna", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Column: Optimization Methodology
s12.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 3.8,
  fill: { color: COLOR_WHITE },
  line: { color: COLOR_LIGHT_GRAY, width: 1 },
  shadow: makeShadow()
});
s12.addShape(pres.shapes.RECTANGLE, {
  x: 0.6, y: 1.3, w: 4.1, h: 0.08,
  fill: { color: COLOR_TEAL },
  line: { style: "none" }
});
s12.addText("Bayesian Optimization Strategy", {
  x: 0.9, y: 1.5, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});
s12.addText([
  { text: "Optuna TPE Search\n", options: { bold: true, color: COLOR_NAVY, fontSize: 13 } },
  { text: "Used Bayesian Tree-structured Parzen Estimator (TPE) search to locate optimal learning rates, tree sizes, and regularization parameter combinations.\n\n", options: { color: COLOR_SLATE, fontSize: 11 } },
  { text: "1-in-8 Data Downsampling\n", options: { bold: true, color: COLOR_NAVY, fontSize: 13 } },
  { text: "Tuned on a statistically representative downsampled subset (187k rows) to reduce search time by 20x, then retrained on the full 2 million row history.\n\n", options: { color: COLOR_SLATE, fontSize: 11 } },
  { text: "Regressed for RMSE\n", options: { bold: true, color: COLOR_NAVY, fontSize: 13 } },
  { text: "Optimized model's Root Mean Squared Error to tighten forecast curve predictions and naturally increase alarm classification precision.", options: { color: COLOR_SLATE, fontSize: 11 } }
], {
  x: 0.9, y: 2.0, w: 3.5, h: 2.9,
  fontFace: FONT_BODY, margin: 0
});

// Right Column: Best Parameters Cards
s12.addText("Best Parameter Solutions Found", {
  x: 5.2, y: 1.3, w: 4.2, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

// 5m card
s12.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.7, w: 4.2, h: 0.75, fill: { color: COLOR_WHITE }, line: { color: COLOR_LIGHT_GRAY, width: 1 }, shadow: makeShadow() });
s12.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.7, w: 0.08, h: 0.75, fill: { color: COLOR_TEAL }, line: { style: "none" } });
s12.addText("5-Minute Horizon Model Params", { x: 5.4, y: 1.75, w: 3.8, h: 0.2, fontFace: FONT_HEADER, fontSize: 11, color: COLOR_NAVY, bold: true, margin: 0 });
s12.addText("learning_rate: 0.141 | num_leaves: 92 | max_depth: 10 | min_child: 40", { x: 5.4, y: 1.95, w: 3.8, h: 0.45, fontFace: FONT_BODY, fontSize: 9.5, color: COLOR_SLATE, margin: 0 });

// 15m card
s12.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 2.55, w: 4.2, h: 0.75, fill: { color: COLOR_WHITE }, line: { color: COLOR_LIGHT_GRAY, width: 1 }, shadow: makeShadow() });
s12.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 2.55, w: 0.08, h: 0.75, fill: { color: COLOR_TEAL }, line: { style: "none" } });
s12.addText("15-Minute Horizon Model Params", { x: 5.4, y: 2.6, w: 3.8, h: 0.2, fontFace: FONT_HEADER, fontSize: 11, color: COLOR_NAVY, bold: true, margin: 0 });
s12.addText("learning_rate: 0.148 | num_leaves: 102 | max_depth: 9 | min_child: 65", { x: 5.4, y: 2.8, w: 3.8, h: 0.45, fontFace: FONT_BODY, fontSize: 9.5, color: COLOR_SLATE, margin: 0 });

// 30m card
s12.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 3.4, w: 4.2, h: 0.75, fill: { color: COLOR_WHITE }, line: { color: COLOR_LIGHT_GRAY, width: 1 }, shadow: makeShadow() });
s12.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 3.4, w: 0.08, h: 0.75, fill: { color: COLOR_TEAL }, line: { style: "none" } });
s12.addText("30-Minute Horizon Model Params", { x: 5.4, y: 3.45, w: 3.8, h: 0.2, fontFace: FONT_HEADER, fontSize: 11, color: COLOR_NAVY, bold: true, margin: 0 });
s12.addText("learning_rate: 0.034 | num_leaves: 72 | max_depth: 8 | min_child: 65", { x: 5.4, y: 3.65, w: 3.8, h: 0.45, fontFace: FONT_BODY, fontSize: 9.5, color: COLOR_SLATE, margin: 0 });

// 60m card
s12.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 4.25, w: 4.2, h: 0.75, fill: { color: COLOR_WHITE }, line: { color: COLOR_LIGHT_GRAY, width: 1 }, shadow: makeShadow() });
s12.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 4.25, w: 0.08, h: 0.75, fill: { color: COLOR_TEAL }, line: { style: "none" } });
s12.addText("60-Minute Horizon Model Params", { x: 5.4, y: 4.3, w: 3.8, h: 0.2, fontFace: FONT_HEADER, fontSize: 11, color: COLOR_NAVY, bold: true, margin: 0 });
s12.addText("learning_rate: 0.047 | num_leaves: 99 | max_depth: 9 | min_child: 61", { x: 5.4, y: 4.5, w: 3.8, h: 0.45, fontFace: FONT_BODY, fontSize: 9.5, color: COLOR_SLATE, margin: 0 });

// ============================================================================
// Slide 13: Model Performance Comparison (V1 vs V2) (Light Background)
// ============================================================================
let s13 = pres.addSlide();
s13.background = { color: COLOR_OFF_WHITE };

s13.addText("Model Performance Comparison", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Column: Key Takeaways
s13.addText("Optimized Precision Results", {
  x: 0.6, y: 1.2, w: 4.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

s13.addText([
  { text: "Precision Improvement across Horizons\n", options: { bold: true, color: COLOR_TEAL, fontSize: 12 } },
  { text: "Optuna tuning successfully increased model precision to 93.45% for 5m, 94.06% for 15m, 90.79% for 30m, and 84.89% for 60m.\n\n", options: { color: COLOR_SLATE, fontSize: 10.5 } },
  { text: "Reduced False Alarm Rate (FAR)\n", options: { bold: true, color: COLOR_CORAL, fontSize: 12 } },
  { text: "The tuned V2 model achieves extremely low FARs: 0.208% at 5m, 0.179% at 15m, 0.278% at 30m, and 0.438% at 60m. Tighter alarms build operator trust.\n\n", options: { color: COLOR_SLATE, fontSize: 10.5 } },
  { text: "Lower Regression Variance (RMSE)\n", options: { bold: true, color: COLOR_NAVY, fontSize: 12 } },
  { text: "Root Mean Squared Error (RMSE) is reduced at 15m and 30m, meaning predictions stay closer to actual trends under highly dynamic load shifts.", options: { color: COLOR_SLATE, fontSize: 10.5 } }
], {
  x: 0.6, y: 1.7, w: 4.1, h: 3.3,
  fontFace: FONT_BODY, margin: 0
});

// Right Column: Comparative Metrics Table
s13.addText("Comparative Test Set Summary Table", {
  x: 5.1, y: 1.2, w: 4.3, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});

s13.addTable([
  [
    { text: "Horizon & Version", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } },
    { text: "F1-Score", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } },
    { text: "Precision", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } },
    { text: "False Alarm (FAR)", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } },
    { text: "RMSE", options: { bold: true, fill: { color: COLOR_NAVY }, color: COLOR_WHITE } }
  ],
  ["5m V1 Baseline", "93.76%", "93.32%", "0.2129%", "0.251°C"],
  ["5m V2 Tuned", "93.77%", "93.45%", "0.2079%", "0.256°C"],
  ["15m V1 Baseline", "91.86%", "93.37%", "0.2026%", "0.405°C"],
  ["15m V2 Tuned", "91.90%", "94.06%", "0.1790%", "0.403°C"],
  ["30m V1 Baseline", "88.64%", "90.18%", "0.2996%", "0.534°C"],
  ["30m V2 Tuned", "88.84%", "90.79%", "0.2783%", "0.532°C"],
  ["60m V1 Baseline", "81.49%", "84.12%", "0.4707%", "0.681°C"],
  ["60m V2 Tuned", "81.26%", "84.89%", "0.4376%", "0.685°C"]
], {
  x: 5.1, y: 1.7, w: 4.3, h: 3.3,
  fontFace: FONT_BODY, fontSize: 8.5,
  border: { pt: 1, color: COLOR_LIGHT_GRAY },
  fill: { color: COLOR_WHITE }
});

// ============================================================================
// Slide 14: Conclusion & Next Steps (Dark Background)
// ============================================================================
let s14 = pres.addSlide();
s14.background = { color: COLOR_NAVY };

s14.addText("Conclusion & Next Steps", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_WHITE, bold: true, margin: 0
});

const cardW = 2.6;
const cardG = 0.4;
const cardX = 0.6;
const cardY = 1.6;

const steps = [
  { num: "PHASE 1", title: "Operator Simulator", desc: "Deploy the Streamlit real-time simulation tool to train control room operators, establish process workflow, and build user trust." },
  { num: "PHASE 2", title: "Historian Connection", desc: "Integrate model pipeline as a microservice reading OPC UA historian live values (1-minute updates) and compute features in real-time." },
  { num: "PHASE 3", title: "Operator UI Alerts", desc: "Render scrolling forecast trends on the operator console, triggering alerts 5 to 60 minutes before threshold crossing." }
];

for (let i = 0; i < 3; i++) {
  let xPos = cardX + i * (cardW + cardG);
  
  s14.addShape(pres.shapes.RECTANGLE, {
    x: xPos, y: cardY, w: cardW, h: 3.2,
    fill: { color: "111E38" },  // slightly lighter navy
    line: { color: COLOR_TEAL, width: 1 }
  });
  
  s14.addText(steps[i].num, {
    x: xPos + 0.1, y: cardY + 0.2, w: cardW - 0.2, h: 0.3,
    fontFace: FONT_HEADER, fontSize: 12, color: COLOR_TEAL, bold: true, align: "center", margin: 0
  });
  
  s14.addText(steps[i].title, {
    x: xPos + 0.1, y: cardY + 0.6, w: cardW - 0.2, h: 0.4,
    fontFace: FONT_HEADER, fontSize: 16, color: COLOR_WHITE, bold: true, align: "center", margin: 0
  });
  
  s14.addText(steps[i].desc, {
    x: xPos + 0.15, y: cardY + 1.2, w: cardW - 0.3, h: 1.8,
    fontFace: FONT_BODY, fontSize: 12, color: COLOR_LIGHT_BLUE, align: "left", margin: 0
  });
}

// Write to files
const outputPath = path.join(__dirname, "docs", "Presentation.pptx");
pres.writeFile({ fileName: outputPath })
  .then(() => {
    console.log("Presentation generated successfully at: " + outputPath);
  })
  .catch((err) => {
    console.error("Error writing file:", err);
  });


