"""Google OR-Tools CP-SAT Solver for N-Queens."""

import time
from datetime import datetime
from typing import Optional, List, Dict, Any

from ortools.sat.python import cp_model
from .model import SolverResult, SolverStatus, BoardSolution
from .validation import validate_solution


def solve_nqueens_cp_sat(
    n: int,
    formulation: str = "alldifferent",
    timeout_seconds: Optional[float] = 60.0,
    threads: int = 0,
    seed: int = 0,
    experiment_id: str = "default_exp"
) -> SolverResult:
    """Solve N-Queens using Google OR-Tools CP-SAT.

    Supported formulations:
    - 'alldifferent': Canonical 1D CP formulation.
      Variables: q_0..q_{n-1} in [0, n-1].
      Constraints:
        - AddAllDifferent(q)
        - AddAllDifferent(q_i + i)
        - AddAllDifferent(q_i - i)
      Features extremely strong filtering via Régin's AllDifferent propagation.

    - 'boolean_2d': 2D Boolean matrix formulation (equivalent to 0-1 MIP).
      Variables: x_{i,j} in {0, 1}.
      Constraints:
        - Exactly one per row / column.
        - At most one per diagonal / anti-diagonal.

    Args:
        n: Board dimension.
        formulation: 'alldifferent' or 'boolean_2d'.
        timeout_seconds: Time limit in seconds.
        threads: Number of search workers (0 = auto).
        seed: Random seed for search randomization.
        experiment_id: Experiment ID.

    Returns:
        SolverResult containing metrics, timing, status, and validated solution.
    """
    timestamp = datetime.now().isoformat()
    t_build_start = time.perf_counter()

    model = cp_model.CpModel()
    q_vars = []
    matrix_vars = {}

    if formulation == "alldifferent":
        # 1D Formulation
        q_vars = [model.new_int_var(0, n - 1, f"q_{i}") for i in range(n)]

        # Unique columns
        model.add_all_different(q_vars)

        # Unique main diagonals (q_i - i)
        model.add_all_different([q_vars[i] - i for i in range(n)])

        # Unique anti diagonals (q_i + i)
        model.add_all_different([q_vars[i] + i for i in range(n)])

        num_vars = n
        num_constrs = 3  # 3 global all_different constraints

    elif formulation == "boolean_2d":
        # 2D Boolean Formulation
        for i in range(n):
            for j in range(n):
                matrix_vars[i, j] = model.new_bool_var(f"x_{i}_{j}")

        num_constrs = 0

        # Row constraints
        for i in range(n):
            model.add_exactly_one([matrix_vars[i, j] for j in range(n)])
            num_constrs += 1

        # Column constraints
        for j in range(n):
            model.add_exactly_one([matrix_vars[i, j] for i in range(n)])
            num_constrs += 1

        # Main diagonals
        for d in range(-(n - 2), n - 1):
            diag = [matrix_vars[i, i - d] for i in range(n) if 0 <= i - d < n]
            if len(diag) >= 2:
                model.add_at_most_one(diag)
                num_constrs += 1

        # Anti diagonals
        for s in range(1, 2 * n - 2):
            anti = [matrix_vars[i, s - i] for i in range(n) if 0 <= s - i < n]
            if len(anti) >= 2:
                model.add_at_most_one(anti)
                num_constrs += 1

        num_vars = n * n

    else:
        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="CP",
            solver_name="cp-sat",
            solver_version="ortools-9.15",
            status=SolverStatus.ERROR,
            error_message=f"Unknown CP-SAT formulation '{formulation}'"
        )

    t_build_end = time.perf_counter()
    build_time = t_build_end - t_build_start

    # Configure solver
    solver = cp_model.CpSolver()
    if timeout_seconds is not None and timeout_seconds > 0:
        solver.parameters.max_time_in_seconds = float(timeout_seconds)
    if threads > 0:
        solver.parameters.num_workers = threads
    if seed != 0:
        solver.parameters.random_seed = seed

    # Solve
    t_solve_start = time.perf_counter()
    status_code = solver.solve(model)
    t_solve_end = time.perf_counter()
    solve_time = t_solve_end - t_solve_start

    status_name = solver.status_name(status_code)

    if status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        queens: List[Optional[int]] = [None] * n
        if formulation == "alldifferent":
            queens = [int(solver.value(q_vars[i])) for i in range(n)]
        else:
            for i in range(n):
                for j in range(n):
                    if solver.value(matrix_vars[i, j]) == 1:
                        queens[i] = j

        sol = BoardSolution(n=n, queens=queens)
        is_valid, val_msg = validate_solution(n, sol)

        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="CP",
            solver_name="cp-sat",
            solver_version="ortools-9.15",
            encoding=formulation,
            seed=seed,
            status=SolverStatus.OPTIMAL,
            num_variables=num_vars,
            num_constraints=num_constrs,
            model_build_time_seconds=build_time,
            solve_time_seconds=solve_time,
            total_time_seconds=build_time + solve_time,
            timeout_seconds=timeout_seconds,
            solution_valid=is_valid,
            solution=sol,
            error_message=None if is_valid else val_msg,
            extra_metrics={
                "branches": solver.num_branches,
                "conflicts": solver.num_conflicts,
                "wall_time": solver.wall_time
            }
        )

    elif status_code == cp_model.INFEASIBLE:
        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="CP",
            solver_name="cp-sat",
            solver_version="ortools-9.15",
            encoding=formulation,
            seed=seed,
            status=SolverStatus.UNSATISFIABLE,
            num_variables=num_vars,
            num_constraints=num_constrs,
            model_build_time_seconds=build_time,
            solve_time_seconds=solve_time,
            total_time_seconds=build_time + solve_time,
            timeout_seconds=timeout_seconds,
            solution_valid=True if n in (2, 3) else False,
            error_message="Proved infeasible"
        )

    elif status_name in ("UNKNOWN", "FEASIBLE") and solve_time >= (timeout_seconds or 60.0) * 0.95:
        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="CP",
            solver_name="cp-sat",
            solver_version="ortools-9.15",
            encoding=formulation,
            seed=seed,
            status=SolverStatus.TIMEOUT,
            num_variables=num_vars,
            num_constraints=num_constrs,
            model_build_time_seconds=build_time,
            solve_time_seconds=solve_time,
            total_time_seconds=build_time + solve_time,
            timeout_seconds=timeout_seconds,
            error_message="CP-SAT time limit reached"
        )

    else:
        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="CP",
            solver_name="cp-sat",
            solver_version="ortools-9.15",
            encoding=formulation,
            seed=seed,
            status=SolverStatus.UNKNOWN,
            num_variables=num_vars,
            num_constraints=num_constrs,
            model_build_time_seconds=build_time,
            solve_time_seconds=solve_time,
            total_time_seconds=build_time + solve_time,
            timeout_seconds=timeout_seconds,
            error_message=f"CP-SAT solver finished with status: {status_name}"
        )
