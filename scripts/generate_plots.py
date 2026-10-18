"""Generates publication-quality figures from experimental benchmark data.

Produces both vector PDF and 300-DPI PNG images saved to results/figures/
and paper/figs/.
"""

import os
import sys
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.nqueens.model import BoardSolution
from src.nqueens.sat_solver import solve_nqueens_sat


# Configure publication-quality matplotlib style
plt.rcParams.update({
    "font.size": 11,
    "font.family": "serif",
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "figure.dpi": 300,
    "lines.linewidth": 1.8,
    "lines.markersize": 6,
    "grid.alpha": 0.4,
    "grid.linestyle": "--",
})

FIGURES_DIR = "results/figures"
PAPER_FIGS_DIR = "paper/figs"


def ensure_dirs():
    os.makedirs(FIGURES_DIR, exist_ok=True)
    os.makedirs(PAPER_FIGS_DIR, exist_ok=True)


def save_figure(fig, filename_base: str):
    """Save both PDF and PNG to results/figures and copy to paper/figs."""
    pdf_path = os.path.join(FIGURES_DIR, f"{filename_base}.pdf")
    png_path = os.path.join(FIGURES_DIR, f"{filename_base}.png")
    fig.savefig(pdf_path, bbox_inches="tight", format="pdf")
    fig.savefig(png_path, bbox_inches="tight", dpi=300, format="png")
    shutil.copy2(pdf_path, os.path.join(PAPER_FIGS_DIR, f"{filename_base}.pdf"))
    shutil.copy2(png_path, os.path.join(PAPER_FIGS_DIR, f"{filename_base}.png"))
    print(f"Saved figure: {filename_base}.pdf and {filename_base}.png")
    plt.close(fig)


def plot_exp_a_cnf_scaling(csv_path: str = "results/raw/exp_a_encodings.csv"):
    """Figure 1 & 2: CNF Clauses and Auxiliary Variables Scaling vs N."""
    if not os.path.exists(csv_path):
        print(f"Skipping {csv_path} (file not found)")
        return

    df = pd.read_csv(csv_path)
    df["n"] = pd.to_numeric(df["n"], errors="coerce")
    df["num_clauses"] = pd.to_numeric(df["num_clauses"], errors="coerce")
    df["num_auxiliary_variables"] = pd.to_numeric(df["num_auxiliary_variables"], errors="coerce")
    df["total_time_seconds"] = pd.to_numeric(df["total_time_seconds"], errors="coerce")

    # Plot 1: Clauses vs N (Log scale)
    fig, ax = plt.subplots(figsize=(7, 5))
    markers = {"pairwise": "o", "seqcounter": "s", "commander": "^", "product": "D", "binary": "v"}
    colors = {"pairwise": "#d95f02", "seqcounter": "#1b9e77", "commander": "#7570b3", "product": "#e7298a", "binary": "#66a61e"}

    for enc, grp in df.groupby("encoding"):
        grp = grp.sort_values("n")
        ax.plot(grp["n"], grp["num_clauses"], label=enc.capitalize(),
                marker=markers.get(enc, "o"), color=colors.get(enc, None))

    ax.set_yscale("log")
    ax.set_xlabel("Board Size $N$")
    ax.set_ylabel("Total Number of CNF Clauses (Log Scale)")
    ax.set_title("CNF Clause Growth across SAT Cardinality Encodings")
    ax.grid(True)
    ax.legend()
    save_figure(fig, "fig1_clauses_vs_n")

    # Plot 2: Auxiliary Variables vs N
    fig, ax = plt.subplots(figsize=(7, 5))
    for enc, grp in df.groupby("encoding"):
        grp = grp.sort_values("n")
        ax.plot(grp["n"], grp["num_auxiliary_variables"], label=enc.capitalize(),
                marker=markers.get(enc, "o"), color=colors.get(enc, None))

    ax.set_xlabel("Board Size $N$")
    ax.set_ylabel("Number of Auxiliary Variables")
    ax.set_title("Auxiliary Variables Allocated by Cardinality Encodings")
    ax.grid(True)
    ax.legend()
    save_figure(fig, "fig2_aux_vars_vs_n")

    # Plot 3: Encoding Total Runtime vs N
    fig, ax = plt.subplots(figsize=(7, 5))
    for enc, grp in df.groupby("encoding"):
        grp = grp.sort_values("n")
        ax.plot(grp["n"], grp["total_time_seconds"], label=enc.capitalize(),
                marker=markers.get(enc, "o"), color=colors.get(enc, None))

    ax.set_xlabel("Board Size $N$")
    ax.set_ylabel("Total Execution Time (seconds)")
    ax.set_title("Total Runtime (Build + Solve) vs $N$ for 5 SAT Encodings")
    ax.grid(True)
    ax.legend()
    save_figure(fig, "fig3_encoding_runtime")


def plot_exp_b_sat_solvers(csv_path: str = "results/raw/exp_b_sat_solvers.csv"):
    """Figure 4: PySAT Solver Engines Comparison."""
    if not os.path.exists(csv_path):
        print(f"Skipping {csv_path} (file not found)")
        return

    df = pd.read_csv(csv_path)
    df["n"] = pd.to_numeric(df["n"], errors="coerce")
    df["solve_time_seconds"] = pd.to_numeric(df["solve_time_seconds"], errors="coerce")

    fig, ax = plt.subplots(figsize=(7, 5))
    solver_styles = {
        "glucose4": ("Glucose 4", "#1f77b4", "o"),
        "cadical195": ("CaDiCaL 1.9.5", "#ff7f0e", "s"),
        "minisat22": ("MiniSat 2.2", "#2ca02c", "^"),
        "lingeling": ("Lingeling", "#d62728", "D"),
        "mergesat3": ("MergeSat 3", "#9467bd", "v"),
    }

    for sname, grp in df.groupby("solver_name"):
        grp = grp.sort_values("n")
        label, col, mark = solver_styles.get(sname, (sname, None, "o"))
        ax.plot(grp["n"], grp["solve_time_seconds"], label=label, marker=mark, color=col)

    ax.set_xlabel("Board Size $N$")
    ax.set_ylabel("SAT Solve Time (seconds)")
    ax.set_title("Performance Comparison of SAT Solver Engines (SeqCounter)")
    ax.grid(True)
    ax.legend()
    save_figure(fig, "fig4_sat_solvers_comparison")


def plot_exp_c_paradigms(csv_path: str = "results/raw/exp_c_paradigms.csv"):
    """Figure 5: Cross-Paradigm Runtime Comparison (SAT vs MIP vs CP)."""
    if not os.path.exists(csv_path):
        print(f"Skipping {csv_path} (file not found)")
        return

    df = pd.read_csv(csv_path)
    df["n"] = pd.to_numeric(df["n"], errors="coerce")
    df["total_time_seconds"] = pd.to_numeric(df["total_time_seconds"], errors="coerce")

    fig, ax = plt.subplots(figsize=(8, 5.5))

    # PySAT
    pysat_df = df[(df["method"] == "SAT") & (df["solver_name"] == "glucose4")].sort_values("n")
    if not pysat_df.empty:
        ax.plot(pysat_df["n"], pysat_df["total_time_seconds"], label="PySAT (SeqCounter)",
                marker="o", color="#1b9e77", linewidth=2)

    # Gurobi MIP
    grb_df = df[(df["method"] == "MIP") & (df["solver_name"] == "gurobi") & (df["status"] == "OPTIMAL")].sort_values("n")
    if not grb_df.empty:
        ax.plot(grb_df["n"], grb_df["total_time_seconds"], label="Gurobi MIP (0-1 ILP)",
                marker="s", color="#d95f02", linewidth=2)

    # CP-SAT AllDiff
    cp_all_df = df[(df["solver_name"] == "cp-sat") & (df["encoding"] == "alldifferent") & (df["status"] == "OPTIMAL")].sort_values("n")
    if not cp_all_df.empty:
        ax.plot(cp_all_df["n"], cp_all_df["total_time_seconds"], label="CP-SAT (AllDifferent CP)",
                marker="^", color="#7570b3", linewidth=2)

    # CP-SAT Boolean 2D
    cp_bool_df = df[(df["solver_name"] == "cp-sat") & (df["encoding"] == "boolean_2d") & (df["status"] == "OPTIMAL")].sort_values("n")
    if not cp_bool_df.empty:
        ax.plot(cp_bool_df["n"], cp_bool_df["total_time_seconds"], label="CP-SAT (Boolean 2D)",
                marker="v", color="#e7298a", linestyle="--")

    # CPLEX MIP
    cpx_df = df[(df["solver_name"] == "cplex_mip") & (df["status"] == "OPTIMAL")].sort_values("n")
    if not cpx_df.empty:
        ax.plot(cpx_df["n"], cpx_df["total_time_seconds"], label="CPLEX MIP (Community Ed.)",
                marker="D", color="#66a61e", linestyle=":")

    ax.set_xlabel("Board Size $N$")
    ax.set_ylabel("Total Execution Time (seconds)")
    ax.set_title("Cross-Paradigm Comparison: SAT vs. MIP vs. CP-SAT")
    ax.grid(True)
    ax.legend()
    save_figure(fig, "fig5_paradigm_comparison")


def plot_exp_d_scalability(csv_path: str = "results/raw/exp_d_scalability.csv"):
    """Figure 6: Large Scale Frontier (N up to 500)."""
    if not os.path.exists(csv_path):
        print(f"Skipping {csv_path} (file not found)")
        return

    df = pd.read_csv(csv_path)
    df["n"] = pd.to_numeric(df["n"], errors="coerce")
    df["total_time_seconds"] = pd.to_numeric(df["total_time_seconds"], errors="coerce")

    fig, ax = plt.subplots(figsize=(7, 5))
    # CP-SAT AllDifferent
    cp_df = df[(df["solver_name"] == "cp-sat") & (df["status"] == "OPTIMAL")].sort_values("n")
    if not cp_df.empty:
        ax.plot(cp_df["n"], cp_df["total_time_seconds"], label="OR-Tools CP-SAT (AllDiff)",
                marker="^", color="#7570b3", linewidth=2)

    # SAT SeqCounter
    sat_df = df[(df["solver_name"] == "glucose4") & (df["status"] == "SATISFIABLE")].sort_values("n")
    if not sat_df.empty:
        ax.plot(sat_df["n"], sat_df["total_time_seconds"], label="PySAT Glucose4 (SeqCounter)",
                marker="o", color="#1b9e77", linewidth=2)

    ax.set_xlabel("Board Size $N$")
    ax.set_ylabel("Total Execution Time (seconds)")
    ax.set_title("Scalability Frontier on Massive Instances ($N \\leq 500$)")
    ax.grid(True)
    ax.legend()
    save_figure(fig, "fig6_scalability_frontier")


def plot_chessboard_solution(n: int = 16):
    """Figure 7: High-resolution publication visualization of an actual solved board."""
    res = solve_nqueens_sat(n, encoding="seqcounter", solver_name="glucose4")
    if not res.solution:
        return

    queens = res.solution.queens
    fig, ax = plt.subplots(figsize=(6, 6))

    # Create checkerboard pattern
    board = np.zeros((n, n))
    for r in range(n):
        for c in range(n):
            if (r + c) % 2 == 1:
                board[r, c] = 0.85
            else:
                board[r, c] = 1.0

    ax.imshow(board, cmap="gray", origin="upper", vmin=0, vmax=1)

    # Place queen markers
    for r, c in enumerate(queens):
        ax.plot(c, r, marker="*", color="#d95f02", markersize=14, markeredgecolor="black")

    ax.set_xticks(range(0, n, 2))
    ax.set_yticks(range(0, n, 2))
    ax.set_xticklabels(range(0, n, 2))
    ax.set_yticklabels(range(0, n, 2))
    ax.set_title(f"Validated Solution for $N={n}$ Queens (PySAT SeqCounter)")
    save_figure(fig, f"fig7_chessboard_n{n}")


def generate_all_plots():
    ensure_dirs()
    print("Generating all publication figures...")
    plot_exp_a_cnf_scaling()
    plot_exp_b_sat_solvers()
    plot_exp_c_paradigms()
    plot_exp_d_scalability()
    plot_chessboard_solution(16)
    print("Figure generation complete!")


if __name__ == "__main__":
    generate_all_plots()
