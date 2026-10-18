"""PySAT-based solver for the N-Queens problem."""

import time
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any

from pysat.solvers import Solver
from .model import SolverResult, SolverStatus, BoardSolution
from .encodings import build_nqueens_cnf, var_to_cell
from .validation import validate_solution


SUPPORTED_SAT_SOLVERS = [
    "glucose4",
    "cadical195",
    "cadical153",
    "minisat22",
    "lingeling",
    "mergesat3",
    "glucose3",
    "maplesat",
]


def solve_nqueens_sat(
    n: int,
    encoding: str = "pairwise",
    solver_name: str = "glucose4",
    timeout_seconds: Optional[float] = 60.0,
    seed: int = 0,
    experiment_id: str = "default_exp"
) -> SolverResult:
    """Solve N-Queens using PySAT and a specified Cardinality encoding.

    Args:
        n: Board dimension.
        encoding: AMO encoding name ('pairwise', 'seqcounter', 'commander', 'product', 'binary').
        solver_name: SAT solver engine ('glucose4', 'cadical195', 'minisat22', etc.).
        timeout_seconds: Time limit in seconds.
        seed: Random seed (if supported by solver).
        experiment_id: Identifier for benchmarking.

    Returns:
        SolverResult containing full performance metrics, status, and validated solution.
    """
    timestamp = datetime.now().isoformat()

    if solver_name not in SUPPORTED_SAT_SOLVERS:
        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="SAT",
            solver_name=solver_name,
            solver_version="pysat-1.9",
            encoding=encoding,
            seed=seed,
            status=SolverStatus.ERROR,
            error_message=f"Unsupported SAT solver '{solver_name}'. Supported: {SUPPORTED_SAT_SOLVERS}"
        )

    # 1. Measure CNF Model Construction Time
    t_build_start = time.perf_counter()
    try:
        cnf = build_nqueens_cnf(n=n, encoding_name=encoding)
    except Exception as e:
        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="SAT",
            solver_name=solver_name,
            solver_version="pysat-1.9",
            encoding=encoding,
            seed=seed,
            status=SolverStatus.ERROR,
            error_message=f"CNF construction error: {str(e)}"
        )
    t_build_end = time.perf_counter()
    build_time = t_build_end - t_build_start

    num_vars = cnf.total_vars
    num_aux_vars = cnf.num_aux_vars
    num_clauses = cnf.num_clauses

    # 2. SAT Solving Phase
    timed_out = False
    timer: Optional[threading.Timer] = None
    t_solve_start = time.perf_counter()

    try:
        # Initialize solver
        with Solver(name=solver_name, bootstrap_with=cnf.clauses) as s:
            # Set up timer interrupt if timeout specified
            if timeout_seconds is not None and timeout_seconds > 0:
                def on_timeout():
                    nonlocal timed_out
                    timed_out = True
                    try:
                        s.interrupt()
                    except Exception:
                        pass

                timer = threading.Timer(timeout_seconds, on_timeout)
                timer.daemon = True
                timer.start()

            sat_result = s.solve()

            if timer is not None:
                timer.cancel()

            t_solve_end = time.perf_counter()
            solve_time = t_solve_end - t_solve_start

            if timed_out or sat_result is None:
                return SolverResult(
                    experiment_id=experiment_id,
                    timestamp=timestamp,
                    n=n,
                    method="SAT",
                    solver_name=solver_name,
                    solver_version="pysat-1.9",
                    encoding=encoding,
                    seed=seed,
                    status=SolverStatus.TIMEOUT,
                    num_variables=num_vars,
                    num_auxiliary_variables=num_aux_vars,
                    num_clauses=num_clauses,
                    model_build_time_seconds=build_time,
                    solve_time_seconds=solve_time,
                    total_time_seconds=build_time + solve_time,
                    timeout_seconds=timeout_seconds,
                    solution_valid=None,
                    error_message="Time limit exceeded"
                )

            if not sat_result:
                # UNSATISFIABLE (expected for N=2 and N=3)
                return SolverResult(
                    experiment_id=experiment_id,
                    timestamp=timestamp,
                    n=n,
                    method="SAT",
                    solver_name=solver_name,
                    solver_version="pysat-1.9",
                    encoding=encoding,
                    seed=seed,
                    status=SolverStatus.UNSATISFIABLE,
                    num_variables=num_vars,
                    num_auxiliary_variables=num_aux_vars,
                    num_clauses=num_clauses,
                    model_build_time_seconds=build_time,
                    solve_time_seconds=solve_time,
                    total_time_seconds=build_time + solve_time,
                    timeout_seconds=timeout_seconds,
                    solution_valid=True if n in (2, 3) else False,
                    error_message=None
                )

            # SATISFIABLE: extract assignment
            model = s.get_model()
            queens: List[Optional[int]] = [None] * n
            for lit in model:
                if lit > 0 and lit <= cnf.num_primary_vars:
                    r, c = var_to_cell(lit, n)
                    queens[r] = c

            solution = BoardSolution(n=n, queens=queens)
            is_valid, validation_msg = validate_solution(n, solution)

            return SolverResult(
                experiment_id=experiment_id,
                timestamp=timestamp,
                n=n,
                method="SAT",
                solver_name=solver_name,
                solver_version="pysat-1.9",
                encoding=encoding,
                seed=seed,
                status=SolverStatus.SATISFIABLE,
                num_variables=num_vars,
                num_auxiliary_variables=num_aux_vars,
                num_clauses=num_clauses,
                model_build_time_seconds=build_time,
                solve_time_seconds=solve_time,
                total_time_seconds=build_time + solve_time,
                timeout_seconds=timeout_seconds,
                solution_valid=is_valid,
                solution=solution,
                error_message=None if is_valid else f"Validation failed: {validation_msg}"
            )

    except Exception as e:
        if timer is not None:
            timer.cancel()
        t_solve_end = time.perf_counter()
        solve_time = t_solve_end - t_solve_start
        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="SAT",
            solver_name=solver_name,
            solver_version="pysat-1.9",
            encoding=encoding,
            seed=seed,
            status=SolverStatus.ERROR,
            num_variables=num_vars,
            num_auxiliary_variables=num_aux_vars,
            num_clauses=num_clauses,
            model_build_time_seconds=build_time,
            solve_time_seconds=solve_time,
            total_time_seconds=build_time + solve_time,
            timeout_seconds=timeout_seconds,
            solution_valid=False,
            error_message=f"SAT solver runtime error: {str(e)}"
        )
