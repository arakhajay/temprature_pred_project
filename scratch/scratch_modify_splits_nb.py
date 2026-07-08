import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

nb_path = r"d:\Python-2025\Antigravity\honeywell\Advanced_EDA_Client.ipynb"
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

print(f"Total cells: {len(nb['cells'])}")
found_count = 0

for i, cell in enumerate(nb['cells']):
    source_lines = cell.get("source", [])
    source_text = "".join(source_lines)
    
    if "2024-12-31" in source_text or "2025-06-30" in source_text:
        print(f"\nCell {i:02d}: type={cell['cell_type']}, len={len(source_lines)}")
        print("Original content:")
        print(source_text)
        
        # Replace dates
        new_lines = []
        for line in source_lines:
            new_line = line.replace("2024-12-31 23:59:00", "2025-06-12 23:59:00")
            new_line = new_line.replace("2025-06-30 23:59:00", "2025-08-09 23:59:00")
            new_line = new_line.replace("2024-12-31", "2025-06-12")
            new_line = new_line.replace("2025-06-30", "2025-08-09")
            new_lines.append(new_line)
            
        cell["source"] = new_lines
        print("Updated content:")
        print("".join(new_lines))
        found_count += 1

print(f"\nUpdated {found_count} cells.")

with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook Advanced_EDA_Client.ipynb updated successfully.")
