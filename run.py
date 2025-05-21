import subprocess
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def run_streamlit():
    script_path = resource_path("main.py")
    subprocess.run(["streamlit", "run", script_path])


if __name__ == "__main__":
    run_streamlit()

    #pyinstaller --onefile --windowed --collect-all streamlit --add-data "main.py;." run.py
