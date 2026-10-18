"""Tests for the PySAT solver module."""

import pytest
from src.nqueens.sat_solver import solve_nqueens_sat, SUPPORTED_SAT_SOLVERS
from src.nqueens.model import SolverStatus


def test_sat_solver_n1():
    res = solve_nqueens_sat(1, encoding="pairwise", solver_name="glucose4")
    assert res.status == SolverStatus.SATISFIABLE
    assert res.solution_valid is True
    assert res.solution.queens == [0]


def test_sat_solver_n2_n3_unsat():
    for n in (2, 3):
        res = solve_nqueens_sat(n, encoding="pairwise", solver_name="glucose4")
        assert res.status == SolverStatus.UNSATISFIABLE


def test_sat_solver_n4_valid():
    res = solve_nqueens_sat(4, encoding="pairwise", solver_name="glucose4")
    assert res.status == SolverStatus.SATISFIABLE
    assert res.solution_valid is True
    assert res.num_variables == 16
    assert res.num_clauses > 0
    assert res.solve_time_seconds > 0 or res.solve_time_seconds == 0.0


@pytest.mark.parametrize("solver", ["glucose4", "cadical195", "minisat22"])
def test_sat_solver_engines(solver):
    res = solve_nqueens_sat(8, encoding="seqcounter", solver_name=solver)
    assert res.status == SolverStatus.SATISFIABLE
    assert res.solution_valid is True
    assert res.num_auxiliary_variables > 0


@pytest.mark.parametrize("enc", ["pairwise", "seqcounter", "commander", "product", "binary"])
def test_sat_solver_all_encodings(enc):
    res = solve_nqueens_sat(8, encoding=enc, solver_name="glucose4")
    assert res.status == SolverStatus.SATISFIABLE
    assert res.solution_valid is True
