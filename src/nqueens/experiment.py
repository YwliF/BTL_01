"""Automated experimental benchmark orchestrator for N-Queens."""

import os
import csv
import time
import psutil
from datetime import datetime
from typing import List, Dict, Any, Optional

from .model import SolverResult, SolverStatus
from .sat_solver import solve_nqueens_sat, SUPPORTED_SAT_SOLVERS
from .gurobi_solver import solve_nqueens_gurobi
from .cp_sat_solver import solve_nqueens_cp_sat
from .cplex_solver import solve_nqueens_cplex_mip, solve_nqueens_cplex_cp
from .encodings import AMO_ENCODINGS


CSV_FIELDNAMES = [
    "experiment_id",
    "timestamp",
    "n",
    "method",
    "solver_name",
    "solver_version",
    "encoding",
    "seed",
    "status",
    "num_variables",
    "num_auxiliary_variables",
    "num_clauses",
    "num_constraints",
    "model_build_time_seconds",
    "solve_time_seconds",
    "total_time_seconds",
    "memory_mb",
    "timeout_seconds",
    "solution_valid",
    "error_message",
]


def _get_process_memory_mb() -> float:
    """Return resident set size memory of current process in MB."""
    try:
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except Exception:
        return 0.0


def append_result_to_csv(csv_path: str, result: SolverResult) -> None:
    """Atomically append a single SolverResult row to CSV."""
    file_exists = os.path.exists(csv_path)
    os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)
    with open(csv_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(result.to_dict())


class ExperimentRunner:
    """Manages execution and recording of N-Queens benchmarks."""

    def __init__(self, output_dir: str = "results/raw"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def run_experiment_a_encodings(
        self,
        n_values: List[int],
        encodings: Optional[List[str]] = None,
        solver_name: str = "glucose4",
        timeout: float = 60.0,
        output_file: str = "results/raw/exp_a_encodings.csv"
    ) -> List[SolverResult]:
        """Exp A: Compare SAT cardinality encodings with fixed solver."""
        if encodings is None:
            encodings = list(AMO_ENCODINGS.keys())

        results = []
        for n in n_values:
            for enc in encodings:
                mem_before = _get_process_memory_mb()
                res = solve_nqueens_sat(
                    n=n,
                    encoding=enc,
                    solver_name=solver_name,
                    timeout_seconds=timeout,
                    experiment_id="exp_a_encodings"
                )
                res.memory_mb = _get_process_memory_mb()
                append_result_to_csv(output_file, res)
                results.append(res)
                print(f"[Exp A] N={n:3d} | Enc={enc:12s} | Status={res.status.value:10s} | "
                      f"Clauses={res.num_clauses or 0:7d} | Time={res.total_time_seconds or 0:.4f}s")
        return results

    def run_experiment_b_sat_solvers(
        self,
        n_values: List[int],
        solvers: Optional[List[str]] = None,
        encoding: str = "seqcounter",
        timeout: float = 60.0,
        output_file: str = "results/raw/exp_b_sat_solvers.csv"
    ) -> List[SolverResult]:
        """Exp B: Compare SAT solver engines with fixed encoding."""
        if solvers is None:
            solvers = ["glucose4", "cadical195", "minisat22", "lingeling", "mergesat3"]

        results = []
        for n in n_values:
            for sname in solvers:
                res = solve_nqueens_sat(
                    n=n,
                    encoding=encoding,
                    solver_name=sname,
                    timeout_seconds=timeout,
                    experiment_id="exp_b_sat_solvers"
                )
                res.memory_mb = _get_process_memory_mb()
                append_result_to_csv(output_file, res)
                results.append(res)
                print(f"[Exp B] N={n:3d} | Solver={sname:12s} | Status={res.status.value:10s} | "
                      f"SolveTime={res.solve_time_seconds or 0:.4f}s | Valid={res.solution_valid}")
        return results

    def run_experiment_c_paradigms(
        self,
        n_values: List[int],
        timeout: float = 60.0,
        output_file: str = "results/raw/exp_c_paradigms.csv"
    ) -> List[SolverResult]:
        """Exp C: Cross-paradigm comparison: SAT vs Gurobi MIP vs CP-SAT vs CPLEX."""
        results = []
        for n in n_values:
            # 1. SAT (best encoding: seqcounter)
            res_sat = solve_nqueens_sat(
                n=n,
                encoding="seqcounter",
                solver_name="glucose4",
                timeout_seconds=timeout,
                experiment_id="exp_c_paradigms"
            )
            res_sat.memory_mb = _get_process_memory_mb()
            append_result_to_csv(output_file, res_sat)
            results.append(res_sat)

            # 2. Gurobi MIP
            res_grb = solve_nqueens_gurobi(
                n=n,
                timeout_seconds=timeout,
                experiment_id="exp_c_paradigms"
            )
            res_grb.memory_mb = _get_process_memory_mb()
            append_result_to_csv(output_file, res_grb)
            results.append(res_grb)

            # 3. CP-SAT (AllDifferent)
            res_cp_all = solve_nqueens_cp_sat(
                n=n,
                formulation="alldifferent",
                timeout_seconds=timeout,
                experiment_id="exp_c_paradigms"
            )
            res_cp_all.memory_mb = _get_process_memory_mb()
            append_result_to_csv(output_file, res_cp_all)
            results.append(res_cp_all)

            # 4. CP-SAT (Boolean 2D)
            res_cp_bool = solve_nqueens_cp_sat(
                n=n,
                formulation="boolean_2d",
                timeout_seconds=timeout,
                experiment_id="exp_c_paradigms"
            )
            res_cp_bool.memory_mb = _get_process_memory_mb()
            append_result_to_csv(output_file, res_cp_bool)
            results.append(res_cp_bool)

            # 5. CPLEX MIP
            res_cplex_mip = solve_nqueens_cplex_mip(
                n=n,
                timeout_seconds=timeout,
                experiment_id="exp_c_paradigms"
            )
            res_cplex_mip.memory_mb = _get_process_memory_mb()
            append_result_to_csv(output_file, res_cplex_mip)
            results.append(res_cplex_mip)

            # 6. CPLEX CP
            res_cplex_cp = solve_nqueens_cplex_cp(
                n=n,
                timeout_seconds=timeout,
                experiment_id="exp_c_paradigms"
            )
            res_cplex_cp.memory_mb = _get_process_memory_mb()
            append_result_to_csv(output_file, res_cplex_cp)
            results.append(res_cplex_cp)

            print(f"[Exp C] N={n:3d} | SAT={res_sat.total_time_seconds or 0:.3f}s | "
                  f"Gurobi={res_grb.status.value}({res_grb.total_time_seconds or 0:.3f}s) | "
                  f"CP-SAT-AllDiff={res_cp_all.total_time_seconds or 0:.3f}s | "
                  f"CPLEX-MIP={res_cplex_mip.status.value}")
        return results

    def run_experiment_d_scalability(
        self,
        n_values: List[int],
        timeout: float = 60.0,
        output_file: str = "results/raw/exp_d_scalability.csv"
    ) -> List[SolverResult]:
        """Exp D: Large-scale scalability stress test (up to N=500)."""
        results = []
        for n in n_values:
            # Test CP-SAT AllDifferent
            res_cp = solve_nqueens_cp_sat(
                n=n,
                formulation="alldifferent",
                timeout_seconds=timeout,
                experiment_id="exp_d_scalability"
            )
            res_cp.memory_mb = _get_process_memory_mb()
            append_result_to_csv(output_file, res_cp)
            results.append(res_cp)

            # Test SAT (Sequential Counter)
            res_sat = solve_nqueens_sat(
                n=n,
                encoding="seqcounter",
                solver_name="glucose4",
                timeout_seconds=timeout,
                experiment_id="exp_d_scalability"
            )
            res_sat.memory_mb = _get_process_memory_mb()
            append_result_to_csv(output_file, res_sat)
            results.append(res_sat)

            # Test Gurobi (will hit LICENSE_LIMIT when N > 44 without WLS)
            res_grb = solve_nqueens_gurobi(
                n=n,
                timeout_seconds=timeout,
                experiment_id="exp_d_scalability"
            )
            res_grb.memory_mb = _get_process_memory_mb()
            append_result_to_csv(output_file, res_grb)
            results.append(res_grb)

            print(f"[Exp D] Scalability N={n:4d} | CP-SAT={res_cp.total_time_seconds or 0:.3f}s | "
                  f"SAT={res_sat.status.value}({res_sat.total_time_seconds or 0:.3f}s) | "
                  f"Gurobi={res_grb.status.value}")
        return results

    def run_experiment_e_stability(
        self,
        n: int = 32,
        seeds: Optional[List[int]] = None,
        timeout: float = 60.0,
        output_file: str = "results/raw/exp_e_stability.csv"
    ) -> List[SolverResult]:
        """Exp E: Stability analysis across repeated runs with seeds."""
        if seeds is None:
            seeds = [1, 2, 3, 4, 5]

        results = []
        for seed in seeds:
            for enc in ["pairwise", "seqcounter", "product"]:
                res = solve_nqueens_sat(
                    n=n,
                    encoding=enc,
                    solver_name="glucose4",
                    timeout_seconds=timeout,
                    seed=seed,
                    experiment_id="exp_e_stability"
                )
                res.memory_mb = _get_process_memory_mb()
                append_result_to_csv(output_file, res)
                results.append(res)

            res_cp = solve_nqueens_cp_sat(
                n=n,
                formulation="alldifferent",
                timeout_seconds=timeout,
                seed=seed,
                experiment_id="exp_e_stability"
            )
            res_cp.memory_mb = _get_process_memory_mb()
            append_result_to_csv(output_file, res_cp)
            results.append(res_cp)
            print(f"[Exp E] Seed={seed} N={n} completed")
        return results
