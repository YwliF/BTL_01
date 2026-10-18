"""Automated LaTeX compilation script for the Elsevier paper."""

import os
import sys
import subprocess
import shutil

PAPER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "paper"))


def compile_paper() -> bool:
    print(f"Compiling LaTeX document in: {PAPER_DIR}")
    os.chdir(PAPER_DIR)

    if not os.path.exists("main.tex"):
        print("Error: paper/main.tex not found.")
        return False

    cmds = [
        ["pdflatex", "-interaction=nonstopmode", "-disable-installer", "main.tex"],
        ["bibtex", "main"],
        ["pdflatex", "-interaction=nonstopmode", "-disable-installer", "main.tex"],
        ["pdflatex", "-interaction=nonstopmode", "-disable-installer", "main.tex"],
    ]

    for step_num, cmd in enumerate(cmds, 1):
        print(f"[{step_num}/4] Running {' '.join(cmd)}...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0 and step_num in (1, 3, 4):
            # Check if PDF was nevertheless generated
            if not os.path.exists("main.pdf"):
                print(f"Error during step {step_num}: returncode={res.returncode}")
                print("Output tail:\n", res.stdout[-800:])
                print("Error output:\n", res.stderr[-800:])
                return False

    if os.path.exists("main.pdf"):
        size_kb = os.path.getsize("main.pdf") / 1024
        print(f"\n>>> SUCCESS: paper/main.pdf generated successfully ({size_kb:.1f} KB) <<<")
        return True
    else:
        print("\n>>> FAILED: paper/main.pdf was not produced. <<<")
        return False


if __name__ == "__main__":
    success = compile_paper()
    sys.exit(0 if success else 1)
