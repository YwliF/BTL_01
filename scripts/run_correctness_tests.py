"""Standalone correctness verification script for N-Queens solvers and encodings."""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.nqueens.model import SolverStatus
from src.nqueens.encodings import AMO_ENCODINGS
from src.nqueens.sat_solver import solve_nqueens_sat, SUPPORTED_SAT_SOLVERS
from src.nqueens.gurobi_solver import solve_nqueens_gurobi
from src.nqueens.cp_sat_solver import solve_nqueens_cp_sat
from src.nqueens.cplex_solver import solve_nqueens_cplex_mip, solve_nqueens_cplex_cp
from src.nqueens.validation import validate_solution


def run_all_correctness_checks() -> bool:
    print("=" * 75)
    print("        N-QUEENS COMPREHENSIVE CORRECTNESS TEST SUITE")
    print("=" * 75)

    passed_all = True

    # 1. Test Infeasibility on N=2 and N=3
    print("\n[1] Testing Impossibility on N=2 and N=3 (Must be proved UNSAT):")
    for n in (2, 3):
        for enc in AMO_ENCODINGS.keys():
            res = solve_nqueens_sat(n, encoding=enc, solver_name="glucose4")
            status_ok = (res.status == SolverStatus.UNSATISFIABLE)
            print(f"  - SAT ({enc:10s}) N={n}: {res.status.value:14s} -> {'PASS' if status_ok else 'FAIL'}")
            if not status_ok:
                passed_all = False

        res_grb = solve_nqueens_gurobi(n)
        status_ok = (res_grb.status == SolverStatus.UNSATISFIABLE)
        print(f"  - Gurobi MIP       N={n}: {res_grb.status.value:14s} -> {'PASS' if status_ok else 'FAIL'}")
        if not status_ok:
            passed_all = False

        res_cp = solve_nqueens_cp_sat(n)
        status_ok = (res_cp.status == SolverStatus.UNSATISFIABLE)
        print(f"  - CP-SAT           N={n}: {res_cp.status.value:14s} -> {'PASS' if status_ok else 'FAIL'}")
        if not status_ok:
            passed_all = False

    # 2. Test Solvability and Solution Validity on N=1, 4, 8, 16
    print("\n[2] Testing Solvability and Independent Validation on N in [1, 4, 8, 16]:")
    test_n = [1, 4, 8, 16]
    for n in test_n:
        # Check all encodings
        for enc in AMO_ENCODINGS.keys():
            res = solve_nqueens_sat(n, encoding=enc, solver_name="glucose4")
            ok = (res.status == SolverStatus.SATISFIABLE and res.solution_valid is True)
            print(f"  - SAT ({enc:10s}) N={n:2d}: Valid={str(res.solution_valid):5s} ({res.solve_time_seconds:.4f}s) -> {'PASS' if ok else 'FAIL'}")
            if not ok:
                passed_all = False

        # Gurobi
        res_grb = solve_nqueens_gurobi(n)
        ok = (res_grb.status == SolverStatus.OPTIMAL and res_grb.solution_valid is True)
        print(f"  - Gurobi MIP       N={n:2d}: Valid={str(res_grb.solution_valid):5s} ({res_grb.solve_time_seconds:.4f}s) -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            passed_all = False

        # CP-SAT (AllDifferent)
        res_cp_all = solve_nqueens_cp_sat(n, formulation="alldifferent")
        ok = (res_cp_all.status == SolverStatus.OPTIMAL and res_cp_all.solution_valid is True)
        print(f"  - CP-SAT AllDiff   N={n:2d}: Valid={str(res_cp_all.solution_valid):5s} ({res_cp_all.solve_time_seconds:.4f}s) -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            passed_all = False

        # CP-SAT (Boolean 2D)
        res_cp_bool = solve_nqueens_cp_sat(n, formulation="boolean_2d")
        ok = (res_cp_bool.status == SolverStatus.OPTIMAL and res_cp_bool.solution_valid is True)
        print(f"  - CP-SAT Bool2D    N={n:2d}: Valid={str(res_cp_bool.solution_valid):5s} ({res_cp_bool.solve_time_seconds:.4f}s) -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            passed_all = False

        # CPLEX MIP
        res_cpx_mip = solve_nqueens_cplex_mip(n)
        ok = (res_cpx_mip.status == SolverStatus.OPTIMAL and res_cpx_mip.solution_valid is True)
        print(f"  - CPLEX MIP        N={n:2d}: Valid={str(res_cpx_mip.solution_valid):5s} ({res_cpx_mip.solve_time_seconds:.4f}s) -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            passed_all = False

        # CPLEX CP
        res_cpx_cp = solve_nqueens_cplex_cp(n)
        ok = (res_cpx_cp.status == SolverStatus.OPTIMAL and res_cpx_cp.solution_valid is True)
        print(f"  - CPLEX CP         N={n:2d}: Valid={str(res_cpx_cp.solution_valid):5s} ({res_cpx_cp.solve_time_seconds:.4f}s) -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            passed_all = False

    # 3. Test SAT Engines consistency on N=8
    print("\n[3] Testing SAT Solver Engines consistency on N=8:")
    for solver_name in ["cadical195", "glucose4", "minisat22", "lingeling", "mergesat3"]:
        res = solve_nqueens_sat(8, encoding="seqcounter", solver_name=solver_name)
        ok = (res.status == SolverStatus.SATISFIABLE and res.solution_valid is True)
        print(f"  - SAT Engine {solver_name:12s}: Valid={str(res.solution_valid):5s} -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            passed_all = False

    print("\n" + "=" * 75)
    if passed_all:
        print(">>> ALL CORRECTNESS CHECKS PASSED SUCCESSFULLY! <<<")
    else:
        print(">>> SOME CHECKS FAILED! PLEASE REVIEW OUTPUT ABOVE. <<<")
    print("=" * 75)
    return passed_all


if __name__ == "__main__":
    success = run_all_correctness_checks()
    sys.exit(0 if success else 1)
