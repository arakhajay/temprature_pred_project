import os
import subprocess
import sys
import win32com.client

# Adjust CWD to root if run from inside approch_v3
if os.path.basename(os.getcwd()) == 'approch_v3':
    os.chdir('..')

print("CWD for compilation:", os.getcwd())

# 1. Run Node presentation compiler
print("\\n--- Running PowerPoint Presentation compiler (JS) ---")
result_node = subprocess.run(["node", "approch_v3/create_eda_presentation_v3.js"], capture_output=True, text=True)
print("STDOUT:", result_node.stdout)
print("STDERR:", result_node.stderr)
if result_node.returncode != 0:
    print("PowerPoint generation failed! Exiting.")
    sys.exit(result_node.returncode)

# 2. Run PDF report compiler
print("\\n--- Running PDF Detailed Report compiler (ReportLab) ---")
result_python = subprocess.run([sys.executable, "approch_v3/generate_eda_pdf_report_v3.py"], capture_output=True, text=True)
print("STDOUT:", result_python.stdout)
print("STDERR:", result_python.stderr)
if result_python.returncode != 0:
    print("PDF Report generation failed! Exiting.")
    sys.exit(result_python.returncode)

# 3. Convert PowerPoint to PDF via COM API
print("\\n--- Converting PowerPoint presentation to PDF ---")
pptx_path = os.path.abspath(os.path.join("docs", "EDA_Presentation_v3.pptx"))
pdf_path = os.path.abspath(os.path.join("docs", "EDA_Presentation_v3.pdf"))

if os.path.exists(pptx_path):
    try:
        powerpoint = win32com.client.Dispatch("Powerpoint.Application")
        # To run headless/without window, we can set Visible=False or WithWindow=False
        # Note: PowerPoint COM sometimes requires Visible=True to load slides correctly,
        # but setting WithWindow=False on Presentations.Open generally works.
        powerpoint.Visible = 1
        
        print(f"Opening presentation: {pptx_path}...")
        deck = powerpoint.Presentations.Open(pptx_path, WithWindow=False)
        
        print(f"Exporting to PDF: {pdf_path}...")
        deck.SaveAs(pdf_path, 32)  # 32 is ppSaveAsPDF
        deck.Close()
        powerpoint.Quit()
        print("PowerPoint to PDF conversion completed successfully!")
    except Exception as e:
        print(f"Error during PowerPoint to PDF conversion: {e}")
else:
    print(f"Error: PowerPoint file not found at {pptx_path}")

print("\\nAll documents compiled successfully!")
