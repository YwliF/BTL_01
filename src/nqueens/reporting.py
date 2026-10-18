"""Statistical aggregation, reporting, and LaTeX table export utilities."""

import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional


def load_benchmark_csv(csv_path: str) -> pd.DataFrame:
    """Load and preprocess benchmark CSV data."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Benchmark file '{csv_path}' not found.")
    df = pd.read_csv(csv_path)

    # Convert numeric columns
    numeric_cols = [
        "n", "num_variables", "num_auxiliary_variables", "num_clauses",
        "num_constraints", "model_build_time_seconds", "solve_time_seconds",
        "total_time_seconds", "memory_mb"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def generate_encoding_summary_table(csv_path: str) -> pd.DataFrame:
    """Generate summary table comparing the 5 SAT encodings."""
    df = load_benchmark_csv(csv_path)
    # Filter only solved instances
    summary = df.groupby(["encoding", "n"]).agg(
        num_clauses=("num_clauses", "mean"),
        num_aux_vars=("num_auxiliary_variables", "mean"),
        build_time=("model_build_time_seconds", "mean"),
        solve_time=("solve_time_seconds", "mean"),
        total_time=("total_time_seconds", "mean"),
    ).reset_index()
    return summary


def export_latex_encoding_table(summary_df: pd.DataFrame, n_select: List[int]) -> str:
    """Export summary dataframe to LaTeX tabular format for the Elsevier paper."""
    filtered = summary_df[summary_df["n"].isin(n_select)].sort_values(by=["n", "encoding"])
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Comparison of SAT Encodings on $N$-Queens: CNF Dimensions and Execution Time.}",
        r"\label{tab:encodings_comparison}",
        r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lrrrrrr@{}}",
        r"\toprule",
        r"$N$ & Encoding & Primary Vars & Aux Vars & Clauses & Build Time (s) & Solve Time (s) \\",
        r"\midrule"
    ]

    last_n = None
    for _, row in filtered.iterrows():
        curr_n = int(row['n'])
        n_str = str(curr_n) if curr_n != last_n else ""
        if last_n is not None and curr_n != last_n:
            lines.append(r"\midrule")
        last_n = curr_n

        enc = str(row['encoding']).capitalize()
        primary_vars = curr_n * curr_n
        aux_vars = int(row['num_aux_vars']) if pd.notna(row['num_aux_vars']) else 0
        clauses = int(row['num_clauses']) if pd.notna(row['num_clauses']) else 0
        build_t = f"{row['build_time']:.4f}" if pd.notna(row['build_time']) else "-"
        solve_t = f"{row['solve_time']:.4f}" if pd.notna(row['solve_time']) else "-"

        lines.append(f"{n_str} & {enc} & {primary_vars} & {aux_vars:,} & {clauses:,} & {build_t} & {solve_t} \\\\")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular*}",
        r"\end{table*}"
    ])
    return "\n".join(lines)


def export_latex_paradigm_table(csv_path: str, n_select: List[int]) -> str:
    """Export cross-paradigm comparison (SAT vs Gurobi vs CP-SAT vs CPLEX) to LaTeX."""
    df = load_benchmark_csv(csv_path)
    filtered = df[df["n"].isin(n_select)]

    # Pivot total_time_seconds by n and method/solver
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\caption{Cross-Paradigm Runtime Comparison (seconds) for $N$-Queens: SAT, Gurobi MIP, and CP-SAT.}",
        r"\label{tab:paradigm_comparison}",
        r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}rrrrrr@{}}",
        r"\toprule",
        r"$N$ & PySAT (SeqCounter) & Gurobi MIP & CP-SAT (AllDiff) & CP-SAT (Boolean 2D) & CPLEX MIP \\",
        r"\midrule"
    ]

    for n in sorted(n_select):
        sub = filtered[filtered["n"] == n]

        def get_val(matcher):
            m = sub[matcher(sub)]
            if m.empty:
                return "-"
            row = m.iloc[0]
            if row["status"] in ("SATISFIABLE", "OPTIMAL"):
                return f"{row['total_time_seconds']:.4f}"
            elif row["status"] == "LICENSE_LIMIT":
                return "Lic. Limit"
            elif row["status"] == "TIMEOUT":
                return "Timeout"
            else:
                return row["status"]

        sat_val = get_val(lambda s: s["solver_name"] == "glucose4")
        grb_val = get_val(lambda s: s["solver_name"] == "gurobi")
        cp_alldiff = get_val(lambda s: (s["solver_name"] == "cp-sat") & (s["encoding"] == "alldifferent"))
        cp_bool = get_val(lambda s: (s["solver_name"] == "cp-sat") & (s["encoding"] == "boolean_2d"))
        cplex_val = get_val(lambda s: s["solver_name"] == "cplex_mip")

        lines.append(f"{n} & {sat_val} & {grb_val} & {cp_alldiff} & {cp_bool} & {cplex_val} \\\\")

    lines.extend([
        r"\bottomrule",
        r"\end{tabular*}",
        r"\end{table*}"
    ])
    return "\n".join(lines)
