"""Comprehensive benchmark execution script for N-Queens.

Runs Experiments A through E and records real, reproducible data into CSV files.
"""

import os
import sys
import argparse

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.nqueens.experiment import ExperimentRunner


def main():
    parser = argparse.ArgumentParser(description="Run N-Queens experimental benchmarks.")
    parser.add_argument("--mode", choices=["quick", "full"], default="full",
                        help="'quick' for rapid smoke test, 'full' for publication data.")
    parser.add_argument("--timeout", type=float, default=60.0,
                        help="Timeout in seconds per instance (default: 60s).")
    args = parser.parse_args()

    runner = ExperimentRunner(output_dir="results/raw")

    if args.mode == "quick":
        print("\n=== RUNNING BENCHMARKS IN QUICK DEMO MODE ===")
        n_enc = [4, 8, 16, 24, 32]
        n_solv = [8, 16, 24, 32]
        n_par = [4, 8, 16, 24, 32, 48]
        n_scal = [50, 100, 150]
        seeds = [1, 2]
    else:
        print("\n=== RUNNING FULL PUBLICATION BENCHMARKS ===")
        n_enc = [4, 8, 12, 16, 20, 24, 28, 32, 40, 48, 64, 80, 100]
        n_solv = [8, 16, 24, 32, 48, 64, 80, 100]
        n_par = [4, 8, 12, 16, 20, 24, 28, 32, 40, 44, 48, 64, 80, 100]
        n_scal = [100, 150, 200, 300, 500]
        seeds = [1, 2, 3, 4, 5]

    print("\n>>> EXPERIMENT A: Comparing SAT Encodings (Pairwise, SeqCounter, Commander, Product, Binary)...")
    runner.run_experiment_a_encodings(n_values=n_enc, timeout=args.timeout)

    print("\n>>> EXPERIMENT B: Comparing SAT Solvers (Glucose4, CaDiCaL, MiniSat, Lingeling, MergeSat)...")
    runner.run_experiment_b_sat_solvers(n_values=n_solv, timeout=args.timeout)

    print("\n>>> EXPERIMENT C: Comparing Paradigms (SAT vs Gurobi MIP vs CP-SAT vs CPLEX)...")
    runner.run_experiment_c_paradigms(n_values=n_par, timeout=args.timeout)

    print("\n>>> EXPERIMENT D: Scalability Stress Test (Large N up to 500)...")
    runner.run_experiment_d_scalability(n_values=n_scal, timeout=args.timeout)

    print("\n>>> EXPERIMENT E: Stability and Variance Across Multiple Random Seeds...")
    runner.run_experiment_e_stability(n=32, seeds=seeds, timeout=args.timeout)

    print("\n=== ALL BENCHMARKS COMPLETED SUCCESSFULLY! ===")
    print("Raw CSV files written to: results/raw/")


if __name__ == "__main__":
    main()
