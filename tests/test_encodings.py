"""Tests for the 5 SAT Cardinality encodings."""

import pytest
from src.nqueens.encodings import (
    build_nqueens_cnf,
    AMO_ENCODINGS,
    AuxVarManager,
    encode_alo,
    cell_to_var,
    var_to_cell
)
from pysat.solvers import Solver


def test_cell_var_bijection():
    n = 8
    for r in range(n):
        for c in range(n):
            v = cell_to_var(r, c, n)
            r_out, c_out = var_to_cell(v, n)
            assert (r, c) == (r_out, c_out)


@pytest.mark.parametrize("enc_name", list(AMO_ENCODINGS.keys()))
def test_all_encodings_amo_behavior(enc_name):
    """Test that each AMO encoding allows 0 or 1 true variable, and rejects >= 2."""
    amo_func = AMO_ENCODINGS[enc_name]
    lits = [1, 2, 3, 4, 5]

    # Test 1: Exactly 0 true is allowed by AMO
    mgr = AuxVarManager(start_id=6)
    clauses = amo_func(lits, mgr)
    with Solver(name="glucose4", bootstrap_with=clauses) as s:
        # Assume all negative
        assert s.solve(assumptions=[-x for x in lits]) is True

    # Test 2: Exactly 1 true is allowed by AMO
    for active_lit in lits:
        mgr = AuxVarManager(start_id=6)
        clauses = amo_func(lits, mgr)
        assumps = [active_lit if x == active_lit else -x for x in lits]
        with Solver(name="glucose4", bootstrap_with=clauses) as s:
            assert s.solve(assumptions=assumps) is True

    # Test 3: Any 2 true MUST BE UNSAT
    for i in range(len(lits)):
        for j in range(i + 1, len(lits)):
            mgr = AuxVarManager(start_id=6)
            clauses = amo_func(lits, mgr)
            with Solver(name="glucose4", bootstrap_with=clauses) as s:
                assert s.solve(assumptions=[lits[i], lits[j]]) is False


@pytest.mark.parametrize("enc_name", list(AMO_ENCODINGS.keys()))
def test_nqueens_cnf_n4_satisfiable(enc_name):
    """Verify that every encoding solves N=4 correctly."""
    cnf = build_nqueens_cnf(4, encoding_name=enc_name)
    assert cnf.num_primary_vars == 16
    assert cnf.num_clauses > 0

    with Solver(name="glucose4", bootstrap_with=cnf.clauses) as s:
        sat = s.solve()
        assert sat is True
        model = s.get_model()
        positive_vars = [v for v in model if v > 0 and v <= cnf.num_primary_vars]
        assert len(positive_vars) == 4


@pytest.mark.parametrize("enc_name", list(AMO_ENCODINGS.keys()))
def test_nqueens_cnf_n2_n3_unsatisfiable(enc_name):
    """Verify that N=2 and N=3 are strictly UNSAT under every encoding."""
    for n in (2, 3):
        cnf = build_nqueens_cnf(n, encoding_name=enc_name)
        with Solver(name="glucose4", bootstrap_with=cnf.clauses) as s:
            assert s.solve() is False
