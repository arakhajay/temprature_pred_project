import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

nb_path = "Model_Training_and_Evaluation_Client.ipynb"
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

cell = nb['cells'][12]
print("".join(cell.get("source", [])))
