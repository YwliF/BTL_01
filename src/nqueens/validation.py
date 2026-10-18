"""Independent validator for N-Queens solutions and problem consistency."""

from typing import List, Tuple, Union, Optional
from .model import BoardSolution


def validate_solution(
    n: int,
    solution: Optional[Union[BoardSolution, List[int], List[List[int]]]]
) -> Tuple[bool, str]:
    """Independently validates whether a solution is a correct placement of N queens.

    Rules:
    1. For N=1, the only valid solution is placing 1 queen at (0, 0).
    2. For N=2 and N=3, mathematically NO solution exists. If any solution is provided,
       it is invalid.
    3. For N >= 4:
       - Exactly N queens must be placed.
       - Each row must have exactly one queen.
       - Each column must have exactly one queen.
       - No two queens may share a major diagonal (r - c = const).
       - No two queens may share a minor diagonal (r + c = const).

    Args:
        n: Board dimension N.
        solution: BoardSolution, list of row-to-col integers, or N x N binary matrix.

    Returns:
        (is_valid: bool, message: str)
    """
    if solution is None:
        return False, "Solution is None"

    # Extract queens column positions
    queens_cols: List[int] = []

    if isinstance(solution, BoardSolution):
        if solution.n != n:
            return False, f"BoardSolution dimension {solution.n} does not match expected N={n}"
        if any(c is None for c in solution.queens):
            return False, "BoardSolution contains None positions"
        queens_cols = [int(c) for c in solution.queens if c is not None]

    elif isinstance(solution, list):
        if len(solution) == 0:
            return False, "Solution is an empty list"

        # Check if 2D matrix
        if isinstance(solution[0], list):
            if len(solution) != n:
                return False, f"Matrix row count {len(solution)} != {n}"
            total_queens = 0
            for r in range(n):
                if len(solution[r]) != n:
                    return False, f"Matrix column count at row {r} is {len(solution[r])} != {n}"
                row_queens = [c for c, val in enumerate(solution[r]) if val == 1]
                if len(row_queens) != 1:
                    return False, f"Row {r} does not have exactly 1 queen (found {len(row_queens)})"
                queens_cols.append(row_queens[0])
                total_queens += 1
            if total_queens != n:
                return False, f"Total queens placed is {total_queens} != {n}"
        else:
            # 1D list of column positions
            if len(solution) != n:
                return False, f"List length {len(solution)} != {n}"
            for r, c in enumerate(solution):
                if not isinstance(c, int):
                    return False, f"Column position at row {r} is not an integer: {c}"
                queens_cols.append(c)
    else:
        return False, f"Unsupported solution type: {type(solution)}"

    # Check N=2 and N=3 impossibility
    if n in (2, 3):
        return False, f"N={n} has no valid solution mathematically, but a solution was provided"

    # Check N=1
    if n == 1:
        if queens_cols == [0]:
            return True, "Valid N=1 solution"
        return False, f"Invalid N=1 position: {queens_cols}"

    # Check row bounds
    for r, c in enumerate(queens_cols):
        if c < 0 or c >= n:
            return False, f"Queen at row {r} has out-of-bounds column {c} (must be in [0, {n-1}])"

    # Check column uniqueness (No two queens in same column)
    seen_cols = set()
    for r, c in enumerate(queens_cols):
        if c in seen_cols:
            return False, f"Column conflict: multiple queens in column {c}"
        seen_cols.add(c)

    # Check main diagonals: r - c must be unique
    seen_main_diag = {}
    for r, c in enumerate(queens_cols):
        d = r - c
        if d in seen_main_diag:
            r_prev = seen_main_diag[d]
            return False, f"Main diagonal conflict between queen at ({r_prev}, {queens_cols[r_prev]}) and ({r}, {c})"
        seen_main_diag[d] = r

    # Check anti diagonals: r + c must be unique
    seen_anti_diag = {}
    for r, c in enumerate(queens_cols):
        d = r + c
        if d in seen_anti_diag:
            r_prev = seen_anti_diag[d]
            return False, f"Anti-diagonal conflict between queen at ({r_prev}, {queens_cols[r_prev]}) and ({r}, {c})"
        seen_anti_diag[d] = r

    return True, f"Solution is valid for N={n}"
