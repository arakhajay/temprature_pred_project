import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

nb_path = "Model_Training_and_Evaluation_Client.ipynb"
with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

for idx, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'markdown':
        text = "".join(cell.get('source', []))
        if text.strip().startswith('#'):
            print(f"Cell {idx:02d}: {text.strip().splitlines()[0]}")
