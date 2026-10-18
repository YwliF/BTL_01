"""Gurobi Mixed-Integer Programming (MIP) Solver for N-Queens."""

import os
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    import gurobipy as gp
    from gurobipy import GRB
    GUROBI_AVAILABLE = True
except ImportError:
    GUROBI_AVAILABLE = False
    gp = None
    GRB = None

from .model import SolverResult, SolverStatus, BoardSolution
from .validation import validate_solution


def _create_gurobi_env(time_limit_seconds: Optional[float] = None) -> Any:
    """Create a Gurobi Environment, prioritizing WLS parameters from environment."""
    if not GUROBI_AVAILABLE:
        raise RuntimeError("gurobipy is not installed.")

    # Check for WLS environment variables
    wls_access_id = os.environ.get("GRB_WLSACCESSID") or os.environ.get("WLSACCESSID")
    wls_secret = os.environ.get("GRB_WLSSECRET") or os.environ.get("WLSSECRET")
    license_id_str = os.environ.get("GRB_LICENSEID") or os.environ.get("LICENSEID")

    env_params: Dict[str, Any] = {
        "OutputFlag": 0,
    }

    if time_limit_seconds is not None and time_limit_seconds > 0:
        env_params["TimeLimit"] = float(time_limit_seconds)

    if wls_access_id and wls_secret and license_id_str:
        try:
            license_id = int(license_id_str)
            env_params["WLSACCESSID"] = wls_access_id
            env_params["WLSSECRET"] = wls_secret
            env_params["LICENSEID"] = license_id
        except ValueError:
            pass

    # Initialize empty env and apply params
    env = gp.Env(empty=True)
    for k, v in env_params.items():
        env.setParam(k, v)
    env.start()
    return env


def solve_nqueens_gurobi(
    n: int,
    timeout_seconds: Optional[float] = 60.0,
    threads: int = 0,
    seed: int = 0,
    experiment_id: str = "default_exp"
) -> SolverResult:
    """Solve the N-Queens problem using Gurobi MIP formulation.

    Model:
      Binary variables: x[i, j] in {0, 1} for i, j in [0, N-1]
      Objective: 0 (Feasibility)
      Constraints:
        - Row sum == 1 for each row
        - Column sum == 1 for each col
        - Main diagonal sum <= 1 for each diagonal (len >= 2)
        - Anti-diagonal sum <= 1 for each anti-diagonal (len >= 2)

    Args:
        n: Board dimension.
        timeout_seconds: Time limit in seconds.
        threads: Number of threads (0 for auto).
        seed: Solver seed.
        experiment_id: Experiment run identifier.

    Returns:
        SolverResult with metrics, timing, status, and validated solution.
    """
    timestamp = datetime.now().isoformat()

    if not GUROBI_AVAILABLE:
        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="MIP",
            solver_name="gurobi",
            solver_version="N/A",
            status=SolverStatus.ERROR,
            error_message="gurobipy library is not available"
        )

    solver_version = f"gurobi-{gp.gurobi.version()[0]}.{gp.gurobi.version()[1]}.{gp.gurobi.version()[2]}"

    # 1. Environment initialization and Model Building
    t_build_start = time.perf_counter()
    env = None
    try:
        env = _create_gurobi_env(time_limit_seconds=timeout_seconds)
        if threads > 0:
            env.setParam("Threads", threads)
        if seed != 0:
            env.setParam("Seed", seed)

        model = gp.Model(f"nqueens_mip_{n}", env=env)
        model.setParam("OutputFlag", 0)

        # Variables: N x N binary
        x = {}
        for i in range(n):
            for j in range(n):
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

        # Row constraints: Exactly one queen per row
        for i in range(n):
            model.addConstr(
                gp.quicksum(x[i, j] for j in range(n)) == 1,
                name=f"row_{i}"
            )

        # Column constraints: Exactly one queen per column
        for j in range(n):
            model.addConstr(
                gp.quicksum(x[i, j] for i in range(n)) == 1,
                name=f"col_{j}"
            )

        # Main diagonals: r - c = d, where d in [-(n-2) .. (n-2)]
        for d in range(-(n - 2), n - 1):
            diag_vars = [x[i, i - d] for i in range(n) if 0 <= i - d < n]
            if len(diag_vars) >= 2:
                model.addConstr(gp.quicksum(diag_vars) <= 1, name=f"main_diag_{d}")

        # Anti diagonals: r + c = s, where s in [1 .. 2n-3]
        for s in range(1, 2 * n - 2):
            anti_vars = [x[i, s - i] for i in range(n) if 0 <= s - i < n]
            if len(anti_vars) >= 2:
                model.addConstr(gp.quicksum(anti_vars) <= 1, name=f"anti_diag_{s}")

        model.update()
        num_vars = model.NumVars
        num_constrs = model.NumConstrs

    except gp.GurobiError as ge:
        t_build_end = time.perf_counter()
        if "size-limited license" in str(ge).lower():
            return SolverResult(
                experiment_id=experiment_id,
                timestamp=timestamp,
                n=n,
                method="MIP",
                solver_name="gurobi",
                solver_version=solver_version,
                seed=seed,
                status=SolverStatus.LICENSE_LIMIT,
                num_variables=n * n,
                model_build_time_seconds=t_build_end - t_build_start,
                error_message=f"Model size exceeds size-limited license: {str(ge)}"
            )
        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="MIP",
            solver_name="gurobi",
            solver_version=solver_version,
            seed=seed,
            status=SolverStatus.ERROR,
            error_message=f"Gurobi model build error: {str(ge)}"
        )
    except Exception as e:
        t_build_end = time.perf_counter()
        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="MIP",
            solver_name="gurobi",
            solver_version=solver_version,
            seed=seed,
            status=SolverStatus.ERROR,
            error_message=f"Unexpected error during build: {str(e)}"
        )

    t_build_end = time.perf_counter()
    build_time = t_build_end - t_build_start

    # 2. Optimization Phase
    t_solve_start = time.perf_counter()
    try:
        model.optimize()
        t_solve_end = time.perf_counter()
        solve_time = t_solve_end - t_solve_start

        grb_status = model.Status

        if grb_status in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
            queens: List[Optional[int]] = [None] * n
            for i in range(n):
                for j in range(n):
                    if x[i, j].X > 0.5:
                        queens[i] = j

            sol = BoardSolution(n=n, queens=queens)
            is_valid, val_msg = validate_solution(n, sol)

            result = SolverResult(
                experiment_id=experiment_id,
                timestamp=timestamp,
                n=n,
                method="MIP",
                solver_name="gurobi",
                solver_version=solver_version,
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
                extra_metrics={"simplex_iter": model.IterCount, "node_count": model.NodeCount}
            )
            model.dispose()
            if env:
                env.dispose()
            return result

        elif grb_status == GRB.INFEASIBLE:
            result = SolverResult(
                experiment_id=experiment_id,
                timestamp=timestamp,
                n=n,
                method="MIP",
                solver_name="gurobi",
                solver_version=solver_version,
                seed=seed,
                status=SolverStatus.UNSATISFIABLE,
                num_variables=num_vars,
                num_constraints=num_constrs,
                model_build_time_seconds=build_time,
                solve_time_seconds=solve_time,
                total_time_seconds=build_time + solve_time,
                timeout_seconds=timeout_seconds,
                solution_valid=True if n in (2, 3) else False,
                error_message="Model proved infeasible"
            )
            model.dispose()
            if env:
                env.dispose()
            return result

        elif grb_status == GRB.TIME_LIMIT:
            result = SolverResult(
                experiment_id=experiment_id,
                timestamp=timestamp,
                n=n,
                method="MIP",
                solver_name="gurobi",
                solver_version=solver_version,
                seed=seed,
                status=SolverStatus.TIMEOUT,
                num_variables=num_vars,
                num_constraints=num_constrs,
                model_build_time_seconds=build_time,
                solve_time_seconds=solve_time,
                total_time_seconds=build_time + solve_time,
                timeout_seconds=timeout_seconds,
                solution_valid=None,
                error_message="Gurobi time limit reached"
            )
            model.dispose()
            if env:
                env.dispose()
            return result

        else:
            result = SolverResult(
                experiment_id=experiment_id,
                timestamp=timestamp,
                n=n,
                method="MIP",
                solver_name="gurobi",
                solver_version=solver_version,
                seed=seed,
                status=SolverStatus.UNKNOWN,
                num_variables=num_vars,
                num_constraints=num_constrs,
                model_build_time_seconds=build_time,
                solve_time_seconds=solve_time,
                total_time_seconds=build_time + solve_time,
                timeout_seconds=timeout_seconds,
                error_message=f"Gurobi terminated with status code {grb_status}"
            )
            model.dispose()
            if env:
                env.dispose()
            return result

    except gp.GurobiError as ge:
        t_solve_end = time.perf_counter()
        if "size-limited license" in str(ge).lower():
            status = SolverStatus.LICENSE_LIMIT
        else:
            status = SolverStatus.ERROR
        if env:
            env.dispose()
        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="MIP",
            solver_name="gurobi",
            solver_version=solver_version,
            seed=seed,
            status=status,
            num_variables=num_vars,
            num_constraints=num_constrs,
            model_build_time_seconds=build_time,
            solve_time_seconds=t_solve_end - t_solve_start,
            total_time_seconds=build_time + (t_solve_end - t_solve_start),
            timeout_seconds=timeout_seconds,
            error_message=f"Gurobi optimize error: {str(ge)}"
        )
    except Exception as e:
        t_solve_end = time.perf_counter()
        if env:
            env.dispose()
        return SolverResult(
            experiment_id=experiment_id,
            timestamp=timestamp,
            n=n,
            method="MIP",
            solver_name="gurobi",
            solver_version=solver_version,
            seed=seed,
            status=SolverStatus.ERROR,
            num_variables=num_vars,
            num_constraints=num_constrs,
            model_build_time_seconds=build_time,
            solve_time_seconds=t_solve_end - t_solve_start,
            total_time_seconds=build_time + (t_solve_end - t_solve_start),
            timeout_seconds=timeout_seconds,
            error_message=f"Unexpected error during solve: {str(e)}"
        )
