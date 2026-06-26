import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

nb_path = "Advanced_EDA_Client.ipynb"
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

print(f"Total cells in Advanced_EDA_Client: {len(nb['cells'])}")
for idx in range(70, len(nb['cells'])):
    cell = nb['cells'][idx]
    print(f"\n--- Cell {idx} ({cell['cell_type']}) ---")
    print("".join(cell.get("source", []))[:300])
