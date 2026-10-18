"""Tests for the independent N-Queens validator."""

import pytest
from src.nqueens.validation import validate_solution
from src.nqueens.model import BoardSolution


def test_validator_n1():
    # N=1 single queen at (0, 0) is valid
    assert validate_solution(1, [0])[0] is True
    assert validate_solution(1, [[1]])[0] is True
    assert validate_solution(1, [1])[0] is False


def test_validator_n2_n3_always_invalid():
    # Mathematically N=2 and N=3 have no solutions
    assert validate_solution(2, [0, 1])[0] is False
    assert validate_solution(3, [0, 2, 1])[0] is False


def test_validator_n4_valid_and_invalid():
    # Canonical 4-queens solutions: [1, 3, 0, 2] and [2, 0, 3, 1]
    is_valid, _ = validate_solution(4, [1, 3, 0, 2])
    assert is_valid is True

    is_valid, _ = validate_solution(4, [2, 0, 3, 1])
    assert is_valid is True

    # Invalid cases:
    # 1. Row/Col conflict
    assert validate_solution(4, [0, 0, 2, 3])[0] is False
    # 2. Main diagonal conflict (0,0) and (1,1)
    assert validate_solution(4, [0, 1, 2, 3])[0] is False
    # 3. Anti diagonal conflict (0,1) and (1,0)
    assert validate_solution(4, [1, 0, 2, 3])[0] is False


def test_validator_n8_valid():
    # Known 8-queens solution: [0, 4, 7, 5, 2, 6, 1, 3]
    is_valid, msg = validate_solution(8, [0, 4, 7, 5, 2, 6, 1, 3])
    assert is_valid is True, msg


def test_validator_matrix_input():
    # Matrix representation
    matrix_4 = [
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [1, 0, 0, 0],
        [0, 0, 1, 0],
    ]
    is_valid, msg = validate_solution(4, matrix_4)
    assert is_valid is True, msg


def test_validator_board_solution_object():
    sol = BoardSolution(n=4, queens=[1, 3, 0, 2])
    is_valid, msg = validate_solution(4, sol)
    assert is_valid is True, msg
