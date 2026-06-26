import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

nb_path = "Model_Training_and_Evaluation_Client.ipynb"
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for idx in range(11, 25):
    if idx < len(nb['cells']):
        cell = nb['cells'][idx]
        print(f"\n--- Cell {idx} ({cell['cell_type']}) ---")
        source = "".join(cell.get("source", []))
        lines = source.splitlines()
        print("\n".join(lines[:12]))
        if len(lines) > 12:
            print("...")
