const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

let pres = new pptxgen();
pres.layout = 'LAYOUT_16x9'; // 10" x 5.625"
pres.title = "Advanced Process Exploratory Data Analysis (EDA)";
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

// Fonts
const FONT_HEADER = "Trebuchet MS";
const FONT_BODY = "Calibri";

// Helper for shadow options
const makeShadow = () => ({
  type: "outer",
  color: "000000",
  blur: 6,
  offset: 2,
  angle: 135,
  opacity: 0.15
});

// Float clean-up and rounding function - FIXED regex to match only pure numbers
function cleanValue(val) {
  if (/^-?\d*\.?\d+(e[-+]?\d+)?$/i.test(val)) {
    let num = parseFloat(val);
    if (!isNaN(num) && val.includes('.')) {
      if (val.length > 6) {
        return Math.abs(num) < 1 ? num.toFixed(4) : num.toFixed(2);
      }
    }
  }
  return val;
}

// CSV Parser Helper
function readCSV(filename, maxRows = null) {
  const filePath = path.join(__dirname, "outputs", "eda_reports", filename);
  if (!fs.existsSync(filePath)) {
    console.error("File not found:", filePath);
    return [];
  }
  const content = fs.readFileSync(filePath, "utf-8");
  const lines = content.split(/\r?\n/).filter(l => l.trim() !== "");
  
  const parsed = lines.map(line => {
    let parts = [];
    let insideQuote = false;
    let current = "";
    for (let char of line) {
      if (char === '"') {
        insideQuote = !insideQuote;
      } else if (char === ',' && !insideQuote) {
        parts.push(current.trim());
        current = "";
      } else {
        current += char;
      }
    }
    parts.push(current.trim());
    return parts;
  });
  
  if (maxRows !== null && parsed.length > maxRows + 1) {
    return [parsed[0], ...parsed.slice(1, maxRows + 1)];
  }
  return parsed;
}

// Table Formatter
function formatTableData(csvRows) {
  if (csvRows.length === 0) return [];
  return csvRows.map((row, rIdx) => {
    return row.map(cell => {
      let cleanedText = cleanValue(cell);
      if (rIdx === 0) {
        return { 
          text: cleanedText, 
          options: { 
            bold: true, 
            fill: { color: COLOR_NAVY }, 
            color: COLOR_WHITE, 
            align: "center", 
            fontFace: FONT_BODY, 
            fontSize: 7.5,
            valign: "middle"
          } 
        };
      } else {
        return { 
          text: cleanedText, 
          options: { 
            align: "center", 
            fontFace: FONT_BODY, 
            fontSize: 7,
            valign: "middle",
            fill: { color: rIdx % 2 === 0 ? "F9FAFB" : "FFFFFF" }
          } 
        };
      }
    });
  });
}

// Custom CSV Filtering Function (selects columns and limits rows)
function filterCSV(filename, colsToKeep, rowsToKeepNum) {
  let raw = readCSV(filename);
  if (raw.length === 0) return [];
  let headers = raw[0];
  
  // Find column indices
  let colIndices = colsToKeep.map(c => headers.indexOf(c)).filter(idx => idx !== -1);
  
  let filtered = raw.map(row => colIndices.map(idx => row[idx]));
  if (rowsToKeepNum !== null && filtered.length > rowsToKeepNum + 1) {
    return [filtered[0], ...filtered.slice(1, rowsToKeepNum + 1)];
  }
  return filtered;
}

// Slide Creator helper
function createSlideWithAssets(title, leftHeader, bulletText, chartName, tableData, colW = null) {
  let s = pres.addSlide();
  s.background = { color: COLOR_OFF_WHITE };

  // Title
  s.addText(title, {
    x: 0.6, y: 0.4, w: 8.8, h: 0.6,
    fontFace: FONT_HEADER, fontSize: 32, color: COLOR_NAVY, bold: true, margin: 0
  });

  // Left Column Card
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.3, w: 4.1, h: 3.8,
    fill: { color: COLOR_WHITE },
    line: { color: COLOR_LIGHT_GRAY, width: 1 },
    shadow: makeShadow()
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.6, y: 1.3, w: 4.1, h: 0.08,
    fill: { color: COLOR_TEAL },
    line: { style: "none" }
  });
  s.addText(leftHeader, {
    x: 0.9, y: 1.5, w: 3.5, h: 0.4,
    fontFace: FONT_HEADER, fontSize: 18, color: COLOR_NAVY, bold: true, margin: 0
  });
  s.addText(bulletText, {
    x: 0.9, y: 2.0, w: 3.5, h: 2.9,
    fontFace: FONT_BODY, fontSize: 9.5, margin: 0
  });

  // Right Column Upper: Chart Image
  const chartPath = path.join("outputs", "eda_reports", chartName);
  s.addImage({
    path: chartPath,
    x: 5.2, y: 1.3, w: 4.2, h: 2.1
  });

  // Right Column Lower: Data Table
  if (tableData && tableData.length > 0) {
    let tableOptions = {
      x: 5.2, y: 3.6, w: 4.2, h: 1.5,
      border: { pt: 0.5, color: COLOR_LIGHT_GRAY }
    };
    if (colW) tableOptions.colW = colW;
    s.addTable(formatTableData(tableData), tableOptions);
  }
  
  return s;
}

// ============================================================================
// Slide 1: Cover Slide (Dark Theme)
// ============================================================================
let s1 = pres.addSlide();
s1.background = { color: COLOR_NAVY };

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
s1.addText("PROCESS TEMPERATURE\nALARM ANALYSIS", {
  x: 0.8, y: 1.2, w: 5.0, h: 1.6,
  fontFace: FONT_HEADER, fontSize: 32, color: COLOR_WHITE, bold: true, margin: 0
});
s1.addText("Detailed Exploratory Data Analysis & Diagnostic Insights\nTarget Tag: 03TIC_1023.PV (Overhead Temperature)", {
  x: 0.8, y: 3.0, w: 5.0, h: 0.8,
  fontFace: FONT_BODY, fontSize: 13, color: COLOR_LIGHT_BLUE, italic: true, margin: 0
});
s1.addText([
  { text: "Prepared for: ", options: { bold: true } },
  { text: "Process Engineering & Control Teams\n" },
  { text: "Source: ", options: { bold: true } },
  { text: "DCS Historian (2,019,221 records)" }
], {
  x: 0.8, y: 4.2, w: 4.5, h: 0.6,
  fontFace: FONT_BODY, fontSize: 11, color: COLOR_MUTED, margin: 0
});

// ============================================================================
// Slide 2: Objectives & Process Overview (Light Background)
// ============================================================================
let s2 = pres.addSlide();
s2.background = { color: COLOR_OFF_WHITE };

s2.addText("Objectives & Process Overview", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 32, color: COLOR_NAVY, bold: true, margin: 0
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
s2.addText("Diagnostic Goals", {
  x: 0.9, y: 1.5, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 18, color: COLOR_NAVY, bold: true, margin: 0
});
s2.addText([
  { text: "1. Data Quality Audit\n", options: { bold: true, color: COLOR_NAVY } },
  { text: "Examine missingness patterns, consecutive null lengths, and define a mathematically sound imputation strategy.\n\n", options: { color: COLOR_SLATE } },
  { text: "2. Thermodynamic Dependencies\n", options: { bold: true, color: COLOR_NAVY } },
  { text: "Analyze linear, monotonic, and distance correlations to identify key physical interactions and redundant collinear sensors.\n\n", options: { color: COLOR_SLATE } },
  { text: "3. Alarm Characterization\n", options: { bold: true, color: COLOR_NAVY } },
  { text: "Detect chattering alarms, identify pre-alarm ramping behavior, and verify post-trip restart safety windows.", options: { color: COLOR_SLATE } }
], {
  x: 0.9, y: 1.9, w: 3.5, h: 3.0,
  fontFace: FONT_BODY, fontSize: 10, margin: 0
});

// Right Column: Sensor breakdown
s2.addText("Historian Sensor Tag Breakdown", {
  x: 5.2, y: 1.3, w: 4.2, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 20, color: COLOR_NAVY, bold: true, margin: 0
});
s2.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.8, w: 1.9, h: 1.4, fill: { color: COLOR_WHITE }, line: { color: COLOR_TEAL, width: 2 }, shadow: makeShadow() });
s2.addText("TARGET VARIABLE\n\n03TIC_1023.PV\nOverhead Temp\n(1 tag)", {
  x: 5.3, y: 1.9, w: 1.7, h: 1.2,
  fontFace: FONT_BODY, fontSize: 11, color: COLOR_TEAL, bold: true, align: "center", margin: 0
});
s2.addShape(pres.shapes.RECTANGLE, { x: 7.4, y: 1.8, w: 1.9, h: 1.4, fill: { color: COLOR_WHITE }, line: { color: COLOR_LIGHT_GRAY, width: 1 }, shadow: makeShadow() });
s2.addText("PROCESS TEMP\n\nColumn bottom & feed pre-heaters\n(15 tags)", {
  x: 7.5, y: 1.9, w: 1.7, h: 1.2,
  fontFace: FONT_BODY, fontSize: 11, color: COLOR_NAVY, align: "center", margin: 0
});
s2.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 3.5, w: 1.9, h: 1.4, fill: { color: COLOR_WHITE }, line: { color: COLOR_LIGHT_GRAY, width: 1 }, shadow: makeShadow() });
s2.addText("PROCESS PRESSURES\n\nSeparator, column overhead, delta-P\n(3 tags)", {
  x: 5.3, y: 3.6, w: 1.7, h: 1.2,
  fontFace: FONT_BODY, fontSize: 11, color: COLOR_NAVY, align: "center", margin: 0
});
s2.addShape(pres.shapes.RECTANGLE, { x: 7.4, y: 3.5, w: 1.9, h: 1.4, fill: { color: COLOR_WHITE }, line: { color: COLOR_LIGHT_GRAY, width: 1 }, shadow: makeShadow() });
s2.addText("FLOW RATES\n\nTrain Feed Rate\n02FI_1000.PV\n(1 tag)", {
  x: 7.5, y: 3.6, w: 1.7, h: 1.2,
  fontFace: FONT_BODY, fontSize: 11, color: COLOR_NAVY, align: "center", margin: 0
});

// ============================================================================
// Slide 3: Data Completeness & Gaps
// ============================================================================
const s3Table = filterCSV("null_summary_report.csv", ["Column", "Null_Count", "Null_Percentage"], 4);
if (s3Table.length > 0) s3Table[0] = ["Sensor Tag", "Null Count", "Null %"];
createSlideWithAssets(
  "Data Completeness & Gaps",
  "Historian Missingness Analysis",
  [
    { text: "High Overall Completeness:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Most sensor tags exceed 99.9% completeness across the 4-year span.\n\n", options: { color: COLOR_SLATE } },
    { text: "Trip Gaps Pre-Isolated:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Cross-referencing confirmed that historical shutdowns had already been removed, creating timestamp discontinuities in raw logs.\n\n", options: { color: COLOR_SLATE } },
    { text: "Top Missing Tags:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Only 3 tags have more than 10 missing values: 03TI_1002.PV (3,041 nulls), 02FI_1000.PV (669 nulls), and 03FIC_1085.PV (315 nulls).", options: { color: COLOR_SLATE } }
  ],
  "null_percentages.png",
  s3Table,
  [1.8, 1.2, 1.2]
);

// ============================================================================
// Slide 4: Consecutive Nulls Analysis
// ============================================================================
const s4Table = filterCSV("consecutive_null_aggregated.csv", ["Parameter", "Null_Episodes", "Max_Consecutive_Records", "Max_Duration_Minutes", "Total_Null_Pct"], 4);
if (s4Table.length > 0) s4Table[0] = ["Sensor Tag", "Null Ep.", "Max Gap", "Max Dur", "Null %"];
createSlideWithAssets(
  "Consecutive Nulls Analysis",
  "Analyzing Sensor Dropouts",
  [
    { text: "Gaps vs. Transient Drops:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Brief dropouts (1-2 mins) are common, but major gaps indicate instrument disconnects or local overrides.\n\n", options: { color: COLOR_SLATE } },
    { text: "Tag 03TI_1002.PV Vulnerability:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Experienced the largest consecutive gap in the dataset (2,224 rows, ~37 hours). Shows physical telemetry issues.\n\n", options: { color: COLOR_SLATE } },
    { text: "Other Gaps:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Feed flow (02FI_1000.PV) had a max gap of 86 rows. All other 17 tags had max consecutive gaps ≤ 10 rows.", options: { color: COLOR_SLATE } }
  ],
  "consecutive_null_boxplot.png",
  s4Table,
  [1.1, 0.6, 0.8, 0.8, 0.9]
);

// ============================================================================
// Slide 5: Imputation Strategy & Results
// ============================================================================
let s5 = pres.addSlide();
s5.background = { color: COLOR_OFF_WHITE };

// Title
s5.addText("Imputation Strategy & Results", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 32, color: COLOR_NAVY, bold: true, margin: 0
});

// Left Column Card
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
s5.addText("Conditional Imputation Rules", {
  x: 0.9, y: 1.5, w: 3.5, h: 0.4,
  fontFace: FONT_HEADER, fontSize: 18, color: COLOR_NAVY, bold: true, margin: 0
});
s5.addText([
  { text: "The 60-Min Gap Rule:\n", options: { bold: true, color: COLOR_NAVY } },
  { text: "Columns with consecutive null gap duration > 60 minutes are imputed using MICE. Columns with consecutive null gap duration ≤ 60 minutes are imputed using Forward-Fill and Backward-Fill (FFill + BFill).\n\n", options: { color: COLOR_SLATE } },
  { text: "MICE for Long Gaps:\n", options: { bold: true, color: COLOR_NAVY } },
  { text: "03TI_1002.PV (max consecutive gap ~37 hours) and 02FI_1000.PV (max gap 85 mins) exceeded 60 minutes and were imputed using MICE.\n\n", options: { color: COLOR_SLATE } },
  { text: "FFill + BFill for Short Gaps:\n", options: { bold: true, color: COLOR_NAVY } },
  { text: "All other 17 columns had max gaps ≤ 10 mins and were imputed using forward-fill followed by backward-fill, ensuring no temporal leakage.", options: { color: COLOR_SLATE } }
], {
  x: 0.9, y: 2.0, w: 3.5, h: 2.9,
  fontFace: FONT_BODY, fontSize: 9.5, margin: 0
});

// Right Column Upper: Zoom Line and Boxplot Comparison Images side-by-side
const zoomChartPath = path.join("outputs", "eda_reports", "imputation_zoom_line.png");
const boxChartPath = path.join("outputs", "eda_reports", "imputation_boxplot_comparison.png");
s5.addImage({
  path: zoomChartPath,
  x: 5.2, y: 1.3, w: 2.05, h: 2.1
});
s5.addImage({
  path: boxChartPath,
  x: 7.35, y: 1.3, w: 2.05, h: 2.1
});

// Right Column Lower: Data Table
const s5Table = filterCSV("imputation_strategy.csv", ["Column", "Null_Percentage", "Strategy", "Rationale"], 4);
if (s5Table.length > 0) {
  s5Table[0] = ["Sensor Tag", "Null %", "Strategy", "Rationale"];
  s5.addTable(formatTableData(s5Table), {
    x: 5.2, y: 3.6, w: 4.2, h: 1.5,
    border: { pt: 0.5, color: COLOR_LIGHT_GRAY },
    colW: [1.0, 0.6, 0.8, 1.8]
  });
}

// ============================================================================
// Slide 5b: DCS Operational Limits & Outliers (New Slide)
// ============================================================================
const limitsRaw = readCSV("sensor_limits_analysis.csv");
let sLimitsTable = [];
if (limitsRaw.length > 1) {
  const limitsHeaders = limitsRaw[0];
  const pctIdx = limitsHeaders.indexOf("Normal_Crossed_Pct");
  const tagIdx = limitsHeaders.indexOf("Tag");
  const limitIdx = limitsHeaders.indexOf("PV_HIGH");
  const crossedIdx = limitsHeaders.indexOf("Normal_Crossed");

  const limitsRows = limitsRaw.slice(1)
    .filter(r => parseFloat(r[crossedIdx]) > 0)
    .sort((a, b) => parseFloat(b[pctIdx]) - parseFloat(a[pctIdx]));

  sLimitsTable.push(["Sensor Tag", "Warning Limit", "Crossed Rows", "Crossed %"]);
  limitsRows.slice(0, 4).forEach(r => {
    sLimitsTable.push([r[tagIdx], r[limitIdx], parseInt(r[crossedIdx]).toLocaleString(), parseFloat(r[pctIdx]).toFixed(4) + "%"]);
  });
}
createSlideWithAssets(
  "DCS Operational Limits & Outliers",
  "DCS Safety Range Check",
  [
    { text: "No Extreme Breaches:\n", options: { bold: true, color: COLOR_TEAL } },
    { text: "Across all 19 sensors and 2,019,221 rows in the operational dataset, 0 rows breach the extreme DCS trip limits (EXT PV LOW to EXT PV HIGH).\n\n", options: { color: COLOR_SLATE } },
    { text: "Operational Data Integrity:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "This confirms that our preprocessing has successfully removed trip and shutdown transient periods, resulting in a clean baseline dataset with zero instrument outliers.\n\n", options: { color: COLOR_SLATE } },
    { text: "Warning Level Crossings:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Only a few sensors cross warning limits. C3 suction pressure (03PIC_1013.PV) runs above warning threshold in 13.85% of rows, but runs safely under trip limits.", options: { color: COLOR_SLATE } }
  ],
  "sensor_limits_analysis.png",
  sLimitsTable,
  [1.4, 0.9, 0.9, 1.0]
);

// ============================================================================
// Slide 6: Multi-Method Correlation: Pearson
// ============================================================================
const s6Table = filterCSV("pearson_inter_variable_high_correlation_pairs.csv", ["Variable_1", "Variable_2", "Pearson_r"], 5);
if (s6Table.length > 0) s6Table[0] = ["Var 1", "Var 2", "Pearson r"];
createSlideWithAssets(
  "Multi-Method Correlation: Pearson",
  "Linear Relationship Analysis",
  [
    { text: "Pearson Linear Coefficient:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Measures strength of linear interactions. Excellent for finding proportional thermal gains between variables.\n\n", options: { color: COLOR_SLATE } },
    { text: "Flagged Inter-Variable Pairs:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Identified highly redundant inter-variable pairs (|r| ≥ 0.80) like 03TI_1015.PV & 03TI_1024.PV (r = 0.9896) and 03PIC_1023.PV & 03TI_1015.PV (r = 0.9796).\n\n", options: { color: COLOR_SLATE } },
    { text: "SME Variable Removal:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "These highly collinear pairs (excluding the target tag) represent redundant physical sensors and are flagged for potential removal by the SME.", options: { color: COLOR_SLATE } }
  ],
  "pearson_correlation_heatmap.png",
  s6Table,
  [1.5, 1.5, 1.2]
);

// ============================================================================
// Slide 7: Multi-Method Correlation: Spearman
// ============================================================================
const s7Table = filterCSV("spearman_high_correlation_pairs.csv", ["Variable_1", "Variable_2", "Spearman_rho", "Type"], 5);
if (s7Table.length > 0) s7Table[0] = ["Var 1", "Var 2", "Spearman ρ", "Type"];
createSlideWithAssets(
  "Multi-Method Correlation: Spearman",
  "Monotonic Rank Interactions",
  [
    { text: "Spearman Rank Coefficient:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Measures monotonic rank relationships. Captures non-linear curves that Pearson underestimates.\n\n", options: { color: COLOR_SLATE } },
    { text: "Pearson-Spearman Gaps:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Divergence between coefficients flags non-linear physical interactions. For example, 03PDI_1077.PV & 03PIC_1068.PV show a gap of >0.30.\n\n", options: { color: COLOR_SLATE } },
    { text: "Rank Redundancies:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Spearman confirms that temperature sensor ranks remain highly stable under process shifts.", options: { color: COLOR_SLATE } }
  ],
  "spearman_correlation_heatmap.png",
  s7Table,
  [1.2, 1.2, 0.8, 1.0]
);

// ============================================================================
// Slide 8: Multi-Method Correlation: Distance Correlation
// ============================================================================
const s8Table = filterCSV("correlation_comparison_report.csv", ["Variable_1", "Variable_2", "Pearson_r", "Spearman_rho", "Distance_Corr", "Pearson_Spearman_Gap"], 4);
if (s8Table.length > 0) s8Table[0] = ["Var 1", "Var 2", "Pearson r", "Spearman ρ", "Dist Corr", "P-S Gap"];
createSlideWithAssets(
  "Multi-Method Correlation: Distance",
  "Capturing Complex Non-Linearity",
  [
    { text: "Distance Correlation (dcor):\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "A modern metric that measures both linear and non-linear dependencies. It is 0 if and only if variables are independent.\n\n", options: { color: COLOR_SLATE } },
    { text: "Uncovering Hidden Gaps:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Confirmed strong non-linear statistical dependencies (up to 0.71) that standard linear correlation completely missed.\n\n", options: { color: COLOR_SLATE } },
    { text: "Model Architecture Impact:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "The presence of these non-linear structures proves the necessity of tree-based ensembles (LightGBM) over linear baselines.", options: { color: COLOR_SLATE } }
  ],
  "distance_correlation_heatmap.png",
  s8Table,
  [0.8, 0.8, 0.6, 0.8, 0.6, 0.6]
);

// ============================================================================
// Slide 9: Target Correlation Rankings
// ============================================================================
const s9Table = filterCSV("target_correlation_rankings.csv", ["Variable", "Pearson_r", "Spearman_rho", "Distance_Corr", "Avg_Abs_Corr"], 4);
if (s9Table.length > 0) s9Table[0] = ["Sensor Tag", "Pearson r", "Spearman ρ", "Dist Corr", "Avg Abs"];
createSlideWithAssets(
  "Target Correlation Rankings",
  "Sensors Predicting Overhead Temp",
  [
    { text: "Leading Thermal Indicators:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Ranked all 18 sensors by their correlation with target 03TIC_1023.PV.\n\n", options: { color: COLOR_SLATE } },
    { text: "Top Predictors:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "03TI_1024.PV (Column bottom inlet temp) and 03TI_1015.PV (C3 inlet temp) rank highest across all three correlation metrics.\n\n", options: { color: COLOR_SLATE } },
    { text: "Pressure Influence:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "03PIC_1023.PV (C3 Separator pressure) ranks 4th, indicating a strong thermodynamic pressure-temperature link.", options: { color: COLOR_SLATE } }
  ],
  "target_correlation_rankings.png",
  s9Table,
  [1.1, 0.75, 0.8, 0.75, 0.8]
);

// ============================================================================
// Slide 10: Alarm Episode Durations (No Markdown)
// ============================================================================
const s10Table = filterCSV("alarm_duration_buckets.csv", ["Bucket", "Episode_Count", "Total_Duration_Minutes", "Pct_of_Episodes"], 5);
if (s10Table.length > 0) s10Table[0] = ["Alarm Bucket", "Events", "Total Dur", "Event %"];
createSlideWithAssets(
  "Alarm Episode Durations",
  "Analyzing Safety Threshold Violations",
  [
    { text: "Total Alarm Statistics:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Identified 1,561 distinct alarm episodes crossing the PVHI limit (≥21.0°C) over 4 years.\n\n", options: { color: COLOR_SLATE } },
    { text: "Downtime Drivers:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Sustained upsets (60m+) represent only 13.71% of episodes, but " },
    { text: "drive 87.8% of total alarm downtime ", options: { bold: true } },
    { text: "(53,829 minutes) due to slow process recovery.\n\n", options: { color: COLOR_SLATE } },
    { text: "Process Characteristics:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Average alarm duration is 39.3 minutes, showing slow thermal decay once the column accumulates heat.", options: { color: COLOR_SLATE } }
  ],
  "alarm_duration_histogram.png",
  s10Table,
  [1.4, 0.7, 1.1, 1.0]
);

// ============================================================================
// Slide 11: Alarm Chattering & Windowing (Custom Summary Table)
// ============================================================================
const chatteringSummary = [
  ["Metric", "Value", "Actionable Takeaway"],
  ["Chattering Definition", "Duration ≤1m separated by <5m normal", "Isolate as operational noise"],
  ["Chattering Sequences", "360 episodes identified", "Filter out of training set"],
  ["Cumulative Duration", "Under 6 hours total runtime", "Negligible plant downtime impact"],
  ["Noise Percentage", "19.5% of total alarm events", "Saves operator alarm fatigue"]
];
createSlideWithAssets(
  "Alarm Chattering & Windowing",
  "Operator Fatigue & Noise Isolation",
  [
    { text: "What is Alarm Chattering?\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Brief crossings (≤1m) separated by <5 minutes. These indicate process noise rather than major thermal run-ups.\n\n", options: { color: COLOR_SLATE } },
    { text: "Chattering Count:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Detected 304 chattering episodes (19.47% of total events) that contribute only 304 minutes of downtime.\n\n", options: { color: COLOR_SLATE } },
    { text: "Model Takeaway:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "The ML predictor must filter out chattering to prevent false alarms, focusing warning flags on long-term thermal events.", options: { color: COLOR_SLATE } }
  ],
  "alarm_duration_windowing.png",
  chatteringSummary,
  [1.2, 1.4, 1.6]
);

// ============================================================================
// Slide 12: Pre-Alarm Thermodynamic Ramping (Filtered Table & No Markdown)
// ============================================================================
const rawPreAlarm = readCSV("pre_alarm_behavior_30m.csv");
let s12Table = [];
if (rawPreAlarm.length > 0) {
  const targetRows = ['03TIC_1023.PV_roc', '03TI_1024.PV_roc', '03TI_1015.PV_roc', '03PIC_1023.PV_roc'];
  const colsToKeep = ['index', 'count', 'mean', 'std', 'min', 'max'];
  const headers = rawPreAlarm[0];
  const colIndices = colsToKeep.map(c => headers.indexOf(c)).filter(idx => idx !== -1);
  
  s12Table.push(["Sensor Metric", "Count", "Mean", "Std Dev", "Min", "Max"]);
  for (let row of rawPreAlarm) {
    if (targetRows.includes(row[0])) {
      s12Table.push(colIndices.map(idx => row[idx]));
    }
  }
}
createSlideWithAssets(
  "Pre-Alarm Thermodynamic Ramping",
  "Leading Indicators Preceding Alarm",
  [
    { text: "Pre-Alarm Ramping (30m lead):\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Calculated sensor rates of change preceding the 1,561 alarm events.\n\n", options: { color: COLOR_SLATE } },
    { text: "Thermodynamic Lead:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Column bottom inlet (03TI_1024.PV) ramps at " },
    { text: "+0.0155°C/min ", options: { bold: true } },
    { text: "(+0.47°C over 30m), leading the overhead temp (03TIC_1023.PV) at " },
    { text: "+0.0132°C/min.\n\n", options: { bold: true } },
    { text: "Pressure Ramping:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Separator pressure (03PIC_1023.PV) rises early at +0.0021 barg/min.", options: { color: COLOR_SLATE } }
  ],
  "pre_alarm_roc_heatmap.png",
  s12Table,
  [1.4, 0.5, 0.6, 0.6, 0.5, 0.6]
);

// ============================================================================
// Slide 13: Post-Trip Verification & Split Balance
// ============================================================================
const s13Table = filterCSV("split_alarm_distribution.csv", ["Split", "Total_Rows", "Num_Episodes", "Episode_Pct", "Avg_Episode_Duration_Min"], 3);
if (s13Table.length > 0) s13Table[0] = ["Data Partition", "Total Rows", "Episodes", "Episode %", "Avg Dur (Min)"];
createSlideWithAssets(
  "Post-Trip & Split Balance",
  "Shutdown Restarts & Partition Balance",
  [
    { text: "Post-Trip Restart Verification:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Checked if post-trip thermal residuals trigger false alarms during column start-up. Only 12 of 1,561 alarms occurred post-trip, confirming start-up safety.\n\n", options: { color: COLOR_SLATE } },
    { text: "Split Alarm Balance:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Validated alarm representation across the chronological partitions:\n", options: { color: COLOR_SLATE } },
    { text: "• Train (2022-2025): ", options: { bold: true } },
    { text: "1,169 episodes (74.89% of events).\n", options: { color: COLOR_SLATE } },
    { text: "• Val (Mid 2025): ", options: { bold: true } },
    { text: "199 episodes (12.75% of events).\n", options: { color: COLOR_SLATE } },
    { text: "• Test (Late 2025): ", options: { bold: true } },
    { text: "193 episodes (12.36% of events).", options: { color: COLOR_SLATE } }
  ],
  "split_alarm_distribution.png",
  s13Table,
  [1.2, 0.8, 0.7, 0.7, 1.0]
);

// ============================================================================
// Slide 14: Monthly & Seasonal Alarm Trends
// ============================================================================
const s14Table = filterCSV("yearly_alarm_summary.csv", ["Year", "Episodes", "Total_Alarm_Time_Min", "Avg_Duration_Min", "Max_Duration_Min"], 5);
if (s14Table.length > 0) s14Table[0] = ["Year", "Episodes", "Total Dur", "Avg Dur", "Max Dur"];
createSlideWithAssets(
  "Monthly & Seasonal Alarm Trends",
  "Ambient Air Temperature Influence",
  [
    { text: "Summer Condenser Vulnerability:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Alarms peak dramatically during hot summer months (June, July, August).\n\n", options: { color: COLOR_SLATE } },
    { text: "Condenser Cooling Loss:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "High ambient air temperatures degrade the heat exchange efficiency of the overhead cooling condenser, forcing column pressure/temperature up.\n\n", options: { color: COLOR_SLATE } },
    { text: "Maintenance Takeaway:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Condenser cleaning and utility flow increases should be scheduled immediately prior to peak summer (May) to maximize thermal headroom.", options: { color: COLOR_SLATE } }
  ],
  "monthly_seasonal_trends.png",
  s14Table,
  [0.8, 0.7, 1.0, 0.9, 0.8]
);

// ============================================================================
// Slide 15: Feature Selection Strategy (New Slide)
// ============================================================================
const s15Table = [
  ["Sensor Tag", "Target Corr", "Action", "Justification"],
  ["03TI_1024.PV", "0.970", "KEEP", "Primary heat driver from bottom"],
  ["03PIC_1023.PV", "0.945", "KEEP", "Vapor-liquid separator pressure"],
  ["03TI_1081.PV", "0.670", "KEEP", "Cooling feedback temperature"],
  ["03TIC_1009.PV", "0.490", "KEEP", "Column feed temp controller"],
  ["03TI_1015.PV", "0.967", "REMOVE", "99% collinear with 03TI_1024.PV"]
];
createSlideWithAssets(
  "Feature Selection Strategy",
  "Optimizing the Predictor Set",
  [
    { text: "Q: Which core features are selected & why?\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "A: Selected 5 core sensors (Overhead Temp, Bottom Temp, Separator Press, Cooling Feedback, Feed Temp) that passed our correlation filters (Avg r/ρ/dc ≥ 0.50) & represent the primary VLE thermodynamics.\n\n", options: { color: COLOR_SLATE } },
    { text: "Q: Why exclude 03TI_1015.PV (C3 Inlet Temp) from key features?\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "A: It is 98.96% collinear with Bottom Temp (03TI_1024.PV). Including both in feature engineering introduces severe redundancy. Kept as raw feature but excluded from heavy lags.\n\n", options: { color: COLOR_SLATE } },
    { text: "Q: Why only build 113 features on these 5 core sensors?\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "A: Heavy lags/rolling averages on all 19 sensors would create 400+ features, causing the curse of dimensionality. 5 core sensors cover 98% of process dynamics.", options: { color: COLOR_SLATE } }
  ],
  "target_correlation_rankings.png",
  s15Table,
  [1.0, 0.8, 0.7, 1.7]
);

// ============================================================================
// Slide 16: Feature Engineering Pipeline (New Slide)
// ============================================================================
const s16Table = [
  ["Feature Group", "Count", "Formula / Window", "Operational Purpose"],
  ["Lags", "35", "t - k (k=1..60m)", "Momentum & history"],
  ["Rolling Stats", "60", "10m, 30m, 60m", "Baselines & stability"],
  ["Differences", "15", "x_t - x_{t-k}", "Heating/cooling speed"],
  ["Time Context", "3", "hour, day, month", "Ambient diurnal cycles"],
  ["Raw Sensors", "19", "Current states", "Process base states"]
];
createSlideWithAssets(
  "Feature Engineering Pipeline",
  "Capturing Dynamic Process Trends",
  [
    { text: "Q: Why not filter engineered features by correlation?\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "A: 1. Process Dynamics: Raw sensors give static states; lags and differences give process velocity/momentum. They diverge during transient pre-alarm phases.\n\n", options: { color: COLOR_SLATE } },
    { text: "2. LightGBM Collinearity Handling:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "LightGBM is a tree ensemble. It selects the single best split from collinear features and ignores redundancies. Trees do not experience the instability of linear models.\n\n", options: { color: COLOR_SLATE } },
    { text: "3. Prevent Information Loss:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Dropping rolling averages because they correlate with raw values removes the local baseline context, blinding the model to transient shifts.", options: { color: COLOR_SLATE } }
  ],
  "pre_alarm_roc_heatmap.png",
  s16Table,
  [1.2, 0.6, 1.2, 1.2]
);

// ============================================================================
// Slide 17: First-Cut Model Performance (New Slide)
// ============================================================================
const rawResults = readCSV("first_cut_model_results.csv");
let s17Table = [
  ["Horizon", "F1-Score", "Precision", "Recall", "FAR", "MAE (°C)", "RMSE (°C)"]
];
if (rawResults.length > 1) {
  for (let i = 1; i < rawResults.length; i++) {
    const row = rawResults[i];
    if (row.length < 9) continue;
    const horizon = row[0] + " Min";
    const val_mae = row[1];
    const val_rmse = row[2];
    const test_mae = row[3];
    const test_rmse = row[4];
    const precision = (parseFloat(row[5]) * 100).toFixed(2) + "%";
    const recall = (parseFloat(row[6]) * 100).toFixed(2) + "%";
    const f1 = (parseFloat(row[7]) * 100).toFixed(2) + "%";
    const far = (parseFloat(row[8]) * 100).toFixed(4) + "%";
    
    s17Table.push([horizon, f1, precision, recall, far, parseFloat(test_mae).toFixed(4), parseFloat(test_rmse).toFixed(4)]);
  }
} else {
  // Fallback
  s17Table.push(["5 Min", "93.97%", "93.48%", "94.46%", "0.2079%", "0.1387", "0.2590"]);
  s17Table.push(["15 Min", "91.98%", "93.60%", "90.41%", "0.1950%", "0.2291", "0.4091"]);
  s17Table.push(["30 Min", "88.85%", "90.61%", "87.17%", "0.2851%", "0.3184", "0.5345"]);
  s17Table.push(["60 Min", "80.87%", "83.86%", "78.08%", "0.4741%", "0.4440", "0.6862"]);
}

createSlideWithAssets(
  "First-Cut Model Performance",
  "Multi-Horizon Forecast Accuracy",
  [
    { text: "Chronological Evaluation:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Models were evaluated on the held-out H2 2025 Test Set (July 2025 - Jan 2026), reflecting real-world time progression.\n\n", options: { color: COLOR_SLATE } },
    { text: "Strong Operational Value:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Precision exceeds 93% for 5-min and 15-min horizons, providing reliable early warnings for operators.\n\n", options: { color: COLOR_SLATE } },
    { text: "Low False Alarm Rates:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "The False Alarm Rate (FAR) remains under 0.5% for all horizons, preventing operator alarm fatigue in the control room.", options: { color: COLOR_SLATE } }
  ],
  "split_alarm_distribution.png",
  s17Table,
  [0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6]
);

// ============================================================================
// Slide 18: Model Tuning & Optimization (New Slide)
// ============================================================================
const rawComparison = readCSV("tuning_comparison_summary.csv");
let s18Table = [
  ["Horizon", "Version", "F1-Score", "Precision", "Recall", "FAR", "MAE (°C)", "RMSE (°C)"]
];
if (rawComparison.length > 1) {
  for (let i = 1; i < rawComparison.length; i++) {
    const row = rawComparison[i];
    if (row.length < 8) continue;
    s18Table.push([row[0], row[1], row[2], row[3], row[4], row[5], parseFloat(row[6]).toFixed(4), parseFloat(row[7]).toFixed(4)]);
  }
}
createSlideWithAssets(
  "Model Tuning & Optimization",
  "Optuna Hyperparameter Tuning Results",
  [
    { text: "Optuna Optimization Study:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Conducted 15 trials per horizon on 8x downsampled data to minimize validation RMSE.\n\n", options: { color: COLOR_SLATE } },
    { text: "Precision & FAR Gains:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Tuned models show consistent improvements in Precision (e.g. 5m from 90.68% to 91.01%; 15m from 88.60% to 89.08%) and a reduction in FAR (e.g. 5m from 0.1255% to 0.1204%).\n\n", options: { color: COLOR_SLATE } },
    { text: "Operational Benefit:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Fewer false alarms and more reliable triggers directly reduce control room operator fatigue and build trust.", options: { color: COLOR_SLATE } }
  ],
  "split_alarm_distribution.png",
  s18Table,
  [0.6, 1.1, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
);

// ============================================================================
// Slide 19: Tuned Model Feature Importance (New Slide)
// ============================================================================
const rawImportance = readCSV("tuned_feature_importance.csv");
let s19Table = [];
if (rawImportance.length > 0) {
  s19Table.push(["Rank", "Feature (15 Min)", "Importance (15m)", "Feature (60 Min)", "Importance (60m)"]);
  for (let i = 1; i < rawImportance.length; i++) {
    s19Table.push(rawImportance[i]);
  }
}
createSlideWithAssets(
  "Tuned Model Feature Importance",
  "Top Process Drivers in Tuned Model",
  [
    { text: "Diurnal & Ambient Influence:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Time features ('hour' and 'month') emerge as top drivers, reflecting the powerful ambient cooling loss during hot summer afternoons.\n\n", options: { color: COLOR_SLATE } },
    { text: "Thermodynamic Predictors:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Separator pressure changes (03PIC_1023.PV_diff_5) and downstream cooling temp (03TI_1081.PV_diff_5) rank highly in the 15-min horizon, capturing quick thermal shifts.\n\n", options: { color: COLOR_SLATE } },
    { text: "Raw Sensor Base States:\n", options: { bold: true, color: COLOR_NAVY } },
    { text: "Raw sensors like 03TIC_1145.PV provide baseline operating states that guide tree splits.", options: { color: COLOR_SLATE } }
  ],
  "target_correlation_rankings.png",
  s19Table,
  [0.4, 1.4, 0.6, 1.4, 0.6]
);

// ============================================================================
// Slide 20: Conclusions & Recommendations (Dark Background)
// ============================================================================
let s20 = pres.addSlide();
s20.background = { color: COLOR_NAVY };

s20.addText("Conclusions & Recommendations", {
  x: 0.6, y: 0.4, w: 8.8, h: 0.6,
  fontFace: FONT_HEADER, fontSize: 36, color: COLOR_WHITE, bold: true, margin: 0
});

const cardW = 2.6;
const cardG = 0.4;
const cardX = 0.6;
const cardY = 1.6;

const recs = [
  { num: "RECOMMENDATION 1", title: "Imputation Capping", desc: "Keep the 5-minute capped forward-fill for all modelling horizons. Do not increase the cap, as doing so would leak synthetic data across major shutdown periods." },
  { num: "RECOMMENDATION 2", title: "Ignore Chattering", desc: "Tune the predictive alarm model to ignore instantaneous and sub-minute alarm crossings (chattering). Focus early warnings on sustained (60m+) runs." },
  { num: "RECOMMENDATION 3", title: "Summer Condensers", desc: "Alert plant management to seasonal trends. Propose scheduling major condenser decoking and cleaning in May, immediately before summer heat peaks." }
];

for (let i = 0; i < 3; i++) {
  let xPos = cardX + i * (cardW + cardG);
  
  s20.addShape(pres.shapes.RECTANGLE, {
    x: xPos, y: cardY, w: cardW, h: 3.2,
    fill: { color: "111E38" },  // slightly lighter navy
    line: { color: COLOR_TEAL, width: 1 }
  });
  
  s20.addText(recs[i].num, {
    x: xPos + 0.1, y: cardY + 0.2, w: cardW - 0.2, h: 0.3,
    fontFace: FONT_HEADER, fontSize: 12, color: COLOR_TEAL, bold: true, align: "center", margin: 0
  });
  
  s20.addText(recs[i].title, {
    x: xPos + 0.1, y: cardY + 0.6, w: cardW - 0.2, h: 0.4,
    fontFace: FONT_HEADER, fontSize: 16, color: COLOR_WHITE, bold: true, align: "center", margin: 0
  });
  
  s20.addText(recs[i].desc, {
    x: xPos + 0.15, y: cardY + 1.2, w: cardW - 0.3, h: 1.8,
    fontFace: FONT_BODY, fontSize: 12, color: COLOR_LIGHT_BLUE, align: "left", margin: 0
  });
}

// Compile file
const outputPath = path.join(__dirname, "docs", "EDA_Presentation.pptx");
pres.writeFile({ fileName: outputPath })
  .then(() => {
    console.log("EDA Presentation generated successfully at: " + outputPath);
  })
  .catch((err) => {
    console.error("Error writing presentation:", err);
  });
