import json
import os

nb_path = "Advanced_EDA_Client.ipynb"
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Define the new cells to insert
markdown_source = [
    "---\n",
    "## 3.5. DCS Operational Limits & Outlier Analysis\n",
    "\n",
    "The client provided operational configuration limits for each tag in `03TIC_1023_PVLO_PVHI.csv`. We check:\n",
    "- **Normal Warning Limits (`PV LOW` to `PV HIGH`)**: Check if process variables cross these normal operating thresholds.\n",
    "- **Extreme Trip Limits (`EXT PV LOW` to `EXT PV HIGH`)**: Any crossing of these extreme boundaries represents physical outliers or sensor malfunctions in the operational data.\n",
    "\n",
    "We verify these ranges against the post-trip operational dataset (2,019,221 rows) after trip transients have been cleaned.\n"
]

code_source = [
    "import os\n",
    "import pandas as pd\n",
    "import numpy as np\n",
    "import matplotlib.pyplot as plt\n",
    "\n",
    "# Load limits configuration\n",
    "limits_path = os.path.join(\"03TIC_1023_PVHI\", \"03TIC_1023_PVHI\", \"03TIC_1023_PVLO_PVHI.csv\")\n",
    "limits_df = pd.read_csv(limits_path)\n",
    "\n",
    "results = []\n",
    "for _, row in limits_df.iterrows():\n",
    "    tag_base = row['DCS Tag Name']\n",
    "    tag_col = f\"{tag_base}.PV\"\n",
    "    \n",
    "    if tag_col not in df.columns:\n",
    "        continue\n",
    "        \n",
    "    values = df[tag_col].dropna()\n",
    "    total_non_null = len(values)\n",
    "    if total_non_null == 0:\n",
    "        continue\n",
    "        \n",
    "    # Limits\n",
    "    pv_high = float(row['PV HIGH']) if pd.notnull(row['PV HIGH']) else np.nan\n",
    "    pv_low = float(row['PV LOW']) if pd.notnull(row['PV LOW']) else np.nan\n",
    "    ext_high = float(row['EXT PV HIGH']) if pd.notnull(row['EXT PV HIGH']) else np.nan\n",
    "    ext_low = float(row['EXT PV LOW']) if pd.notnull(row['EXT PV LOW']) else np.nan\n",
    "    \n",
    "    # Check crossings\n",
    "    crossed_high = (values > pv_high).sum() if pd.notnull(pv_high) else 0\n",
    "    crossed_low = (values < pv_low).sum() if pd.notnull(pv_low) else 0\n",
    "    total_crossed = int(crossed_high + crossed_low)\n",
    "    crossed_pct = (total_crossed / total_non_null) * 100\n",
    "    \n",
    "    # Check extreme breaches (outliers)\n",
    "    breached_high = (values > ext_high).sum() if pd.notnull(ext_high) else 0\n",
    "    breached_low = (values < ext_low).sum() if pd.notnull(ext_low) else 0\n",
    "    total_breached = int(breached_high + breached_low)\n",
    "    breached_pct = (total_breached / total_non_null) * 100\n",
    "    \n",
    "    results.append({\n",
    "        'Tag': tag_col,\n",
    "        'Description': row['Description'],\n",
    "        'PV_LOW': pv_low,\n",
    "        'PV_HIGH': pv_high,\n",
    "        'EXT_LOW': ext_low,\n",
    "        'EXT_HIGH': ext_high,\n",
    "        'Total_Rows': total_non_null,\n",
    "        'Normal_Crossed': total_crossed,\n",
    "        'Normal_Crossed_Pct': round(crossed_pct, 6),\n",
    "        'Extreme_Breached': total_breached,\n",
    "        'Extreme_Breached_Pct': round(breached_pct, 6)\n",
    "    })\n",
    "    \n",
    "res_df = pd.DataFrame(results)\n",
    "\n",
    "# Save summary\n",
    "csv_path = os.path.join(OUTPUT_DIR, \"sensor_limits_analysis.csv\")\n",
    "res_df.to_csv(csv_path, index=False)\n",
    "print(f\"Saved: {csv_path}\")\n",
    "\n",
    "# Display summary table for non-zero crossings or all\n",
    "display(res_df[res_df['Normal_Crossed'] > 0].sort_values('Normal_Crossed_Pct', ascending=False))\n",
    "\n",
    "# Plot limits crossings\n",
    "plot_df = res_df[res_df['Normal_Crossed'] > 0].copy()\n",
    "plot_df = plot_df.sort_values('Normal_Crossed_Pct', ascending=True)\n",
    "\n",
    "plt.figure(figsize=(10, 5))\n",
    "colors = ['#0D9488' if pct < 1.0 else '#F96167' for pct in plot_df['Normal_Crossed_Pct']]\n",
    "bars = plt.barh(plot_df['Tag'], plot_df['Normal_Crossed_Pct'], color=colors, edgecolor='none', height=0.5)\n",
    "\n",
    "for bar in bars:\n",
    "    width = bar.get_width()\n",
    '    label_text = f"{width:.6f}%" if width < 0.1 else f"{width:.2f}%"\n',
    "    plt.text(width + 0.1, bar.get_y() + bar.get_height()/2, label_text, \n",
    "             va='center', ha='left', fontsize=10, fontweight='bold', color='#1E293B')\n",
    "             \n",
    "plt.title(\"DCS Normal PV Limit Crossing Rates (%)\", fontsize=14, fontweight='bold', pad=15, color='#0F172A')\n",
    "plt.xlabel(\"Crossing Percentage (%)\", fontsize=11, fontweight='bold', labelpad=10, color='#334155')\n",
    "plt.xlim(0, max(plot_df['Normal_Crossed_Pct'].max() + 2.0, 15.0))\n",
    "plt.grid(axis='x', linestyle='--', alpha=0.5, color='#CBD5E1')\n",
    "\n",
    "ax = plt.gca()\n",
    "ax.spines['top'].set_visible(False)\n",
    "ax.spines['right'].set_visible(False)\n",
    "ax.spines['left'].set_color('#94A3B8')\n",
    "ax.spines['bottom'].set_color('#94A3B8')\n",
    "ax.tick_params(colors='#475569')\n",
    "\n",
    "plt.tight_layout()\n",
    "plot_path = os.path.join(OUTPUT_DIR, \"sensor_limits_analysis.png\")\n",
    "plt.savefig(plot_path, dpi=150, bbox_inches='tight')\n",
    "plt.show()\n"
]

new_markdown_cell = {
    "cell_type": "markdown",
    "id": "dcs_limits_markdown",
    "metadata": {},
    "source": markdown_source
}

new_code_cell = {
    "cell_type": "code",
    "execution_count": None,
    "id": "dcs_limits_code",
    "metadata": {},
    "outputs": [],
    "source": code_source
}

# Find the cell index corresponding to Cell 14 (we saw it is the null percentages bar chart cell)
# Let's verify by finding the cell that plots "null_percentages.png"
target_idx = -1
for idx, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source_text = "".join(cell.get('source', []))
        if 'null_percentages.png' in source_text:
            target_idx = idx
            break

if target_idx != -1:
    print(f"Found target cell at index {target_idx}")
    # Insert right after target_idx
    nb['cells'].insert(target_idx + 1, new_markdown_cell)
    nb['cells'].insert(target_idx + 2, new_code_cell)
    
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1, ensure_ascii=False)
    print("Injected DCS Limits cells successfully.")
else:
    print("Error: Could not find cell with 'null_percentages.png'")
