"""Tests for Gurobi MIP, CP-SAT, and CPLEX solvers."""

import pytest
from src.nqueens.gurobi_solver import solve_nqueens_gurobi
from src.nqueens.cp_sat_solver import solve_nqueens_cp_sat
from src.nqueens.cplex_solver import solve_nqueens_cplex_mip, solve_nqueens_cplex_cp
from src.nqueens.model import SolverStatus


def test_gurobi_n1():
    res = solve_nqueens_gurobi(1)
    assert res.status == SolverStatus.OPTIMAL
    assert res.solution_valid is True
    assert res.solution.queens == [0]


def test_gurobi_n2_n3():
    for n in (2, 3):
        res = solve_nqueens_gurobi(n)
        assert res.status == SolverStatus.UNSATISFIABLE


def test_gurobi_n4():
    res = solve_nqueens_gurobi(4)
    assert res.status == SolverStatus.OPTIMAL
    assert res.solution_valid is True


def test_gurobi_n8():
    res = solve_nqueens_gurobi(8)
    assert res.status == SolverStatus.OPTIMAL
    assert res.solution_valid is True


def test_gurobi_license_limit_handling():
    # N=50 requires 2500 binary variables (> 2000 limit)
    res = solve_nqueens_gurobi(50)
    assert res.status in (SolverStatus.LICENSE_LIMIT, SolverStatus.OPTIMAL)


def test_cp_sat_n1():
    res = solve_nqueens_cp_sat(1)
    assert res.status == SolverStatus.OPTIMAL
    assert res.solution_valid is True
    assert res.solution.queens == [0]


def test_cp_sat_n2_n3():
    for n in (2, 3):
        res = solve_nqueens_cp_sat(n)
        assert res.status == SolverStatus.UNSATISFIABLE


def test_cp_sat_n4_alldiff():
    res = solve_nqueens_cp_sat(4, formulation="alldifferent")
    assert res.status == SolverStatus.OPTIMAL
    assert res.solution_valid is True


def test_cp_sat_n4_boolean():
    res = solve_nqueens_cp_sat(4, formulation="boolean_2d")
    assert res.status == SolverStatus.OPTIMAL
    assert res.solution_valid is True


def test_cp_sat_n8():
    res = solve_nqueens_cp_sat(8)
    assert res.status == SolverStatus.OPTIMAL
    assert res.solution_valid is True


def test_cplex_mip_n4():
    res = solve_nqueens_cplex_mip(4)
    assert res.status == SolverStatus.OPTIMAL
    assert res.solution_valid is True


def test_cplex_cp_n4():
    res = solve_nqueens_cplex_cp(4)
    assert res.status == SolverStatus.OPTIMAL
    assert res.solution_valid is True
