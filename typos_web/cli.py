import os
from pathlib import Path
import sys

def cli():
    python_executable = sys.executable
    args = [
        python_executable,
        "-m",
        "streamlit",
        "run",
        str(Path(__file__).parent / "main.py"),
    ]
    print(f"Python executable: {python_executable}")
    print(f"Running: {args}")
    os.execv(python_executable, args)

if __name__ == "__main__":
    cli()