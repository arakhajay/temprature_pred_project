import subprocess
import time
import sys

notebooks = [
    "approch_v5/Detailed_EDA_v5.ipynb",
    "approch_v5/Feature_Engineering_v5.ipynb",
    "approch_v5/Feature_Selection_v5.ipynb",
    "approch_v5/Models_Training_v5.ipynb",
    "approch_v5/Model_Performance_Comparison_v5.ipynb"
]

print("Starting sequential execution of all V5 notebooks...")

for nb in notebooks:
    print("\n" + "="*41)
    print(f"Executing {nb}...")
    start_time = time.time()
    
    # Run jupyter nbconvert to execute the notebook in place
    cmd = [
        "jupyter", "nbconvert", 
        "--to", "notebook", 
        "--execute", 
        "--inplace", 
        nb
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start_time
    
    if result.returncode == 0:
        print(f"Successfully executed {nb} in {elapsed:.2f} seconds.")
    else:
        print(f"FAILED executing {nb} after {elapsed:.2f} seconds.")
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        sys.exit(1)

print("\nAll notebooks executed successfully and saved in-place!")
