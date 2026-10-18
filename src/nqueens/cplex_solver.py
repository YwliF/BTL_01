"""IBM CPLEX MIP and CP Optimizer Solver for N-Queens."""

import time
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    import docplex.mp.model as mp
    CPLEX_MP_AVAILABLE = True
except ImportError:
    CPLEX_MP_AVAILABLE = False
    mp = None

try:
    import docplex.cp.model as cp
    CPLEX_CP_AVAILABLE = True
except ImportError:
    CPLEX_CP_AVAILABLE = False
    cp = None

from .model import SolverResult, SolverStatus, BoardSolution
from .validation import validate_solution


def solve_nqueens_cplex_mip(
    n: int,
    timeout_seconds: Optional[float] = 60.0,
    seed: int = 0,
    experiment_id: str = "default_exp"
) -> SolverResult:
    """Solve N-Queens using IBM CPLEX MIP (via docplex.mp).

    Handles Community Edition limits (1000 variables/constraints).
    """
    timestamp = datetime.now().isoformat()
    if not CPLEX_MP_AVAILABLE:
        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="MIP",
            solver_name="cplex_mip",
            solver_version="N/A",
            status=SolverStatus.ERROR,
            error_message="docplex.mp is not installed"
        )

    t_build_start = time.perf_counter()
    try:
        model = mp.Model(name=f"nqueens_cplex_mip_{n}")
        model.set_time_limit(timeout_seconds if timeout_seconds else 60.0)

        # Variables: N x N binary
        x = {(i, j): model.binary_var(name=f"x_{i}_{j}") for i in range(n) for j in range(n)}

        # Row constraints
        for i in range(n):
            model.add_constraint(model.sum(x[i, j] for j in range(n)) == 1)

        # Column constraints
        for j in range(n):
            model.add_constraint(model.sum(x[i, j] for i in range(n)) == 1)

        # Main diagonals
        for d in range(-(n - 2), n - 1):
            diag = [x[i, i - d] for i in range(n) if 0 <= i - d < n]
            if len(diag) >= 2:
                model.add_constraint(model.sum(diag) <= 1)

        # Anti diagonals
        for s in range(1, 2 * n - 2):
            anti = [x[i, s - i] for i in range(n) if 0 <= s - i < n]
            if len(anti) >= 2:
                model.add_constraint(model.sum(anti) <= 1)

        num_vars = model.number_of_binary_variables
        num_constrs = model.number_of_constraints

    except Exception as e:
        t_build_end = time.perf_counter()
        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="MIP",
            solver_name="cplex_mip",
            solver_version="cplex-22.2",
            status=SolverStatus.ERROR,
            model_build_time_seconds=t_build_end - t_build_start,
            error_message=f"Model creation error: {str(e)}"
        )

    t_build_end = time.perf_counter()
    build_time = t_build_end - t_build_start

    # Solve
    t_solve_start = time.perf_counter()
    try:
        sol = model.solve(log_output=False)
        t_solve_end = time.perf_counter()
        solve_time = t_solve_end - t_solve_start

        if sol is None:
            # Check if infeasible (N=2, 3) or timeout
            status_str = model.solve_details.status
            if n in (2, 3) or "infeasible" in status_str.lower():
                return SolverResult(
                    experiment_id=experiment_id,
                    timestamp=timestamp,
                    n=n,
                    method="MIP",
                    solver_name="cplex_mip",
                    solver_version="cplex-22.2",
                    seed=seed,
                    status=SolverStatus.UNSATISFIABLE,
                    num_variables=num_vars,
                    num_constraints=num_constrs,
                    model_build_time_seconds=build_time,
                    solve_time_seconds=solve_time,
                    total_time_seconds=build_time + solve_time,
                    solution_valid=True if n in (2, 3) else False
                )
            return SolverResult(
                experiment_id=experiment_id,
                timestamp=timestamp,
                n=n,
                method="MIP",
                solver_name="cplex_mip",
                solver_version="cplex-22.2",
                seed=seed,
                status=SolverStatus.TIMEOUT,
                num_variables=num_vars,
                num_constraints=num_constrs,
                model_build_time_seconds=build_time,
                solve_time_seconds=solve_time,
                total_time_seconds=build_time + solve_time,
                error_message=f"CPLEX MIP solve returned None: {status_str}"
            )

        queens: List[Optional[int]] = [None] * n
        for i in range(n):
            for j in range(n):
                if sol.get_value(x[i, j]) > 0.5:
                    queens[i] = j

        board_sol = BoardSolution(n=n, queens=queens)
        is_valid, val_msg = validate_solution(n, board_sol)

        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="MIP",
            solver_name="cplex_mip",
            solver_version="cplex-22.2",
            seed=seed,
            status=SolverStatus.OPTIMAL,
            num_variables=num_vars,
            num_constraints=num_constrs,
            model_build_time_seconds=build_time,
            solve_time_seconds=solve_time,
            total_time_seconds=build_time + solve_time,
            timeout_seconds=timeout_seconds,
            solution_valid=is_valid,
            solution=board_sol,
            error_message=None if is_valid else val_msg
        )

    except Exception as e:
        t_solve_end = time.perf_counter()
        err_msg = str(e)
        if "size limit" in err_msg.lower() or "1000" in err_msg:
            status = SolverStatus.LICENSE_LIMIT
        else:
            status = SolverStatus.ERROR

        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="MIP",
            solver_name="cplex_mip",
            solver_version="cplex-22.2",
            seed=seed,
            status=status,
            num_variables=num_vars,
            num_constraints=num_constrs,
            model_build_time_seconds=build_time,
            solve_time_seconds=t_solve_end - t_solve_start,
            total_time_seconds=build_time + (t_solve_end - t_solve_start),
            error_message=err_msg
        )


def solve_nqueens_cplex_cp(
    n: int,
    timeout_seconds: Optional[float] = 60.0,
    seed: int = 0,
    experiment_id: str = "default_exp"
) -> SolverResult:
    """Solve N-Queens using IBM CP Optimizer (via docplex.cp)."""
    timestamp = datetime.now().isoformat()
    if not CPLEX_CP_AVAILABLE:
        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="CP",
            solver_name="cplex_cp",
            solver_version="N/A",
            status=SolverStatus.ERROR,
            error_message="docplex.cp is not installed"
        )

    t_build_start = time.perf_counter()
    try:
        model = cp.CpoModel(name=f"nqueens_cplex_cp_{n}")
        q = [model.integer_var(0, n - 1, name=f"q_{i}") for i in range(n)]

        model.add(cp.all_diff(q))
        model.add(cp.all_diff([q[i] + i for i in range(n)]))
        model.add(cp.all_diff([q[i] - i for i in range(n)]))

        num_vars = n
        num_constrs = 3
    except Exception as e:
        t_build_end = time.perf_counter()
        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="CP",
            solver_name="cplex_cp",
            solver_version="cplex-22.2",
            status=SolverStatus.ERROR,
            model_build_time_seconds=t_build_end - t_build_start,
            error_message=f"Model creation error: {str(e)}"
        )

    t_build_end = time.perf_counter()
    build_time = t_build_end - t_build_start

    t_solve_start = time.perf_counter()
    try:
        msol = model.solve(TimeLimit=timeout_seconds if timeout_seconds else 60.0, LogVerbosity="Quiet")
        t_solve_end = time.perf_counter()
        solve_time = t_solve_end - t_solve_start

        if not msol or not msol.is_solution():
            return SolverResult(
                experiment_id=experiment_id,
                timestamp=timestamp,
                n=n,
                method="CP",
                solver_name="cplex_cp",
                solver_version="cplex-22.2",
                seed=seed,
                status=SolverStatus.UNSATISFIABLE if n in (2, 3) else SolverStatus.TIMEOUT,
                num_variables=num_vars,
                num_constraints=num_constrs,
                model_build_time_seconds=build_time,
                solve_time_seconds=solve_time,
                total_time_seconds=build_time + solve_time,
                solution_valid=True if n in (2, 3) else None
            )

        queens = [int(msol.get_value(q[i])) for i in range(n)]
        board_sol = BoardSolution(n=n, queens=queens)
        is_valid, val_msg = validate_solution(n, board_sol)

        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="CP",
            solver_name="cplex_cp",
            solver_version="cplex-22.2",
            seed=seed,
            status=SolverStatus.OPTIMAL,
            num_variables=num_vars,
            num_constraints=num_constrs,
            model_build_time_seconds=build_time,
            solve_time_seconds=solve_time,
            total_time_seconds=build_time + solve_time,
            solution_valid=is_valid,
            solution=board_sol,
            error_message=None if is_valid else val_msg
        )
    except Exception as e:
        t_solve_end = time.perf_counter()
        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="CP",
            solver_name="cplex_cp",
            solver_version="cplex-22.2",
            status=SolverStatus.ERROR,
            error_message=str(e),
            solve_time_seconds=t_solve_end - t_solve_start
        )
