import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# Paths
DATA_PATH = r"d:\Python-2025\Antigravity\honeywell\03TIC_1023_PVHI\03TIC_1023_PVHI\03TIC_1023_Final_merged_TripDataRemoved.parquet"
LIMITS_PATH = r"d:\Python-2025\Antigravity\honeywell\03TIC_1023_PVHI\03TIC_1023_PVHI\03TIC_1023_PVLO_PVHI.csv"
OUTPUT_DIR = r"d:\Python-2025\Antigravity\honeywell\outputs\eda_reports"

def main():
    print("Loading data...")
    df = pd.read_parquet(DATA_PATH)
    limits_df = pd.read_csv(LIMITS_PATH)
    
    results = []
    for _, row in limits_df.iterrows():
        tag_base = row['DCS Tag Name']
        tag_col = f"{tag_base}.PV"
        
        if tag_col not in df.columns:
            continue
            
        values = df[tag_col].dropna()
        total_non_null = len(values)
        if total_non_null == 0:
            continue
            
        # Limits
        pv_high = float(row['PV HIGH']) if pd.notnull(row['PV HIGH']) else np.nan
        pv_low = float(row['PV LOW']) if pd.notnull(row['PV LOW']) else np.nan
        ext_high = float(row['EXT PV HIGH']) if pd.notnull(row['EXT PV HIGH']) else np.nan
        ext_low = float(row['EXT PV LOW']) if pd.notnull(row['EXT PV LOW']) else np.nan
        
        # Check crossings
        crossed_high = (values > pv_high).sum() if pd.notnull(pv_high) else 0
        crossed_low = (values < pv_low).sum() if pd.notnull(pv_low) else 0
        total_crossed = int(crossed_high + crossed_low)
        crossed_pct = (total_crossed / total_non_null) * 100
        
        # Check extreme breaches (outliers)
        breached_high = (values > ext_high).sum() if pd.notnull(ext_high) else 0
        breached_low = (values < ext_low).sum() if pd.notnull(ext_low) else 0
        total_breached = int(breached_high + breached_low)
        breached_pct = (total_breached / total_non_null) * 100
        
        results.append({
            'Tag': tag_col,
            'Description': row['Description'],
            'PV_LOW': pv_low,
            'PV_HIGH': pv_high,
            'EXT_LOW': ext_low,
            'EXT_HIGH': ext_high,
            'Total_Rows': total_non_null,
            'Normal_Crossed': total_crossed,
            'Normal_Crossed_Pct': round(crossed_pct, 6),
            'Extreme_Breached': total_breached,
            'Extreme_Breached_Pct': round(breached_pct, 6)
        })
        
    res_df = pd.DataFrame(results)
    
    # Save CSV
    csv_path = os.path.join(OUTPUT_DIR, "sensor_limits_analysis.csv")
    res_df.to_csv(csv_path, index=False)
    print(f"Saved: {csv_path}")
    
    # Generate visualization
    # Filter for sensors that actually have > 0 normal crossings
    plot_df = res_df[res_df['Normal_Crossed'] > 0].copy()
    plot_df = plot_df.sort_values('Normal_Crossed_Pct', ascending=True)
    
    plt.figure(figsize=(10, 5))
    colors = ['#0D9488' if pct < 1.0 else '#F96167' for pct in plot_df['Normal_Crossed_Pct']]
    
    bars = plt.barh(plot_df['Tag'], plot_df['Normal_Crossed_Pct'], color=colors, edgecolor='none', height=0.5)
    
    # Add values on bars
    for bar in bars:
        width = bar.get_width()
        label_text = f"{width:.6f}%" if width < 0.1 else f"{width:.2f}%"
        plt.text(width + 0.1, bar.get_y() + bar.get_height()/2, label_text, 
                 va='center', ha='left', fontsize=10, fontweight='bold', color='#1E293B')
                 
    plt.title("DCS Normal PV Limit Crossing Rates (%)", fontsize=14, fontweight='bold', pad=15, color='#0F172A')
    plt.xlabel("Crossing Percentage (%)", fontsize=11, fontweight='bold', labelpad=10, color='#334155')
    plt.xlim(0, max(plot_df['Normal_Crossed_Pct'].max() + 2.0, 15.0))
    plt.grid(axis='x', linestyle='--', alpha=0.5, color='#CBD5E1')
    
    # Clean spines
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#94A3B8')
    ax.spines['bottom'].set_color('#94A3B8')
    ax.tick_params(colors='#475569')
    
    plt.tight_layout()
    plot_path = os.path.join(OUTPUT_DIR, "sensor_limits_analysis.png")
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved visualization: {plot_path}")

if __name__ == "__main__":
    main()
