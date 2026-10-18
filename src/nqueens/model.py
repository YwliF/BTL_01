"""Data structures and representations for the N-Queens problem."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import json


class SolverStatus(str, Enum):
    """Execution status returned by solvers."""
    SATISFIABLE = "SATISFIABLE"
    OPTIMAL = "OPTIMAL"
    UNSATISFIABLE = "UNSATISFIABLE"
    TIMEOUT = "TIMEOUT"
    LICENSE_LIMIT = "LICENSE_LIMIT"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

    @property
    def is_solved(self) -> bool:
        """Return True if a satisfying / optimal solution was found."""
        return self in (SolverStatus.SATISFIABLE, SolverStatus.OPTIMAL)

    @property
    def is_infeasible(self) -> bool:
        """Return True if proved infeasible."""
        return self == SolverStatus.UNSATISFIABLE


@dataclass
class BoardSolution:
    """Chessboard representation of an N-Queens solution."""
    n: int
    # queens[r] = c means a queen is placed at row r, column c
    # If no queen in row r, queens[r] is None or empty.
    queens: List[Optional[int]]

    def to_matrix(self) -> List[List[int]]:
        """Return an N x N binary matrix where matrix[r][c] == 1 iff queen at (r, c)."""
        matrix = [[0] * self.n for _ in range(self.n)]
        for r, c in enumerate(self.queens):
            if c is not None and 0 <= c < self.n:
                matrix[r][c] = 1
        return matrix

    def to_ascii(self) -> str:
        """Return ASCII art of the chessboard."""
        lines = []
        for r in range(self.n):
            row_chars = []
            for c in range(self.n):
                if self.queens[r] == c:
                    row_chars.append("Q")
                else:
                    row_chars.append(".")
            lines.append(" ".join(row_chars))
        return "\n".join(lines)


@dataclass
class SolverResult:
    """Detailed benchmark metrics and results from a solver run."""
    experiment_id: str
    timestamp: str
    n: int
    method: str  # "SAT", "MIP", "CP"
    solver_name: str
    solver_version: str
    encoding: Optional[str] = None
    seed: Optional[int] = 0
    status: SolverStatus = SolverStatus.UNKNOWN
    num_variables: Optional[int] = None
    num_auxiliary_variables: Optional[int] = None
    num_clauses: Optional[int] = None
    num_constraints: Optional[int] = None
    model_build_time_seconds: Optional[float] = None
    solve_time_seconds: Optional[float] = None
    total_time_seconds: Optional[float] = None
    memory_mb: Optional[float] = None
    timeout_seconds: Optional[float] = None
    solution_valid: Optional[bool] = None
    solution: Optional[BoardSolution] = None
    error_message: Optional[str] = None
    extra_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to a flat dictionary suitable for CSV export."""
        return {
            "experiment_id": self.experiment_id,
            "timestamp": self.timestamp,
            "n": self.n,
            "method": self.method,
            "solver_name": self.solver_name,
            "solver_version": self.solver_version,
            "encoding": self.encoding or "N/A",
            "seed": self.seed if self.seed is not None else "N/A",
            "status": self.status.value,
            "num_variables": self.num_variables if self.num_variables is not None else "",
            "num_auxiliary_variables": self.num_auxiliary_variables if self.num_auxiliary_variables is not None else "",
            "num_clauses": self.num_clauses if self.num_clauses is not None else "",
            "num_constraints": self.num_constraints if self.num_constraints is not None else "",
            "model_build_time_seconds": f"{self.model_build_time_seconds:.6f}" if self.model_build_time_seconds is not None else "",
            "solve_time_seconds": f"{self.solve_time_seconds:.6f}" if self.solve_time_seconds is not None else "",
            "total_time_seconds": f"{self.total_time_seconds:.6f}" if self.total_time_seconds is not None else "",
            "memory_mb": f"{self.memory_mb:.2f}" if self.memory_mb is not None else "",
            "timeout_seconds": self.timeout_seconds if self.timeout_seconds is not None else "",
            "solution_valid": self.solution_valid if self.solution_valid is not None else "",
            "error_message": self.error_message or "",
        }
