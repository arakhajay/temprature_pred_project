import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

nb_path = "Advanced_EDA_Client.ipynb"
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

cell = nb['cells'][70]
print("".join(cell.get("source", []))[:1000])
if len("".join(cell.get("source", []))) > 1000:
    print("...")
