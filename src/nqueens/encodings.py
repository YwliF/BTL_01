"""SAT Encodings for the N-Queens Problem.

Implements Cardinality Constraints (At-Least-One, At-Most-One, Exactly-One)
using five major SAT encoding strategies:
1. Pairwise Encoding (Naive)
2. Sequential Counter Encoding (Sinz, CP 2005)
3. Commander Variable Encoding (Klieber & Kwon, 2007)
4. Product Encoding (Chen, 2010)
5. Binary / Bitwise Encoding (Frisch et al., 2005)

Every CNF formula generated tracks:
- Primary variables: N^2 board positions
- Auxiliary variables: introduced by the specific AMO encoding
- Total clauses count
- Clause list in DIMACS format (integers, negative for negation)
"""

import math
from typing import List, Tuple, Dict, Any, Callable
from dataclasses import dataclass, field
import time


@dataclass
class CNFFormula:
    """Represents a Conjunctive Normal Form (CNF) formula."""
    n: int
    encoding_name: str
    num_primary_vars: int
    num_aux_vars: int
    clauses: List[List[int]] = field(default_factory=list)
    build_time_seconds: float = 0.0

    @property
    def total_vars(self) -> int:
        return self.num_primary_vars + self.num_aux_vars

    @property
    def num_clauses(self) -> int:
        return len(self.clauses)


class AuxVarManager:
    """Manages unique variable indices for SAT formulas."""
    def __init__(self, start_id: int):
        self._next_id = start_id
        self._initial_id = start_id

    def allocate(self, count: int = 1) -> List[int]:
        """Allocate 'count' new auxiliary variable IDs."""
        ids = list(range(self._next_id, self._next_id + count))
        self._next_id += count
        return ids

    def allocate_one(self) -> int:
        """Allocate a single new auxiliary variable ID."""
        vid = self._next_id
        self._next_id += 1
        return vid

    @property
    def count(self) -> int:
        """Total number of auxiliary variables allocated."""
        return self._next_id - self._initial_id


# ---------------------------------------------------------------------------
# Cardinality Encodings (AMO: At-Most-One, ALO: At-Least-One, EO: Exactly-One)
# ---------------------------------------------------------------------------

def encode_alo(lits: List[int]) -> List[List[int]]:
    """At-Least-One (ALO): at least one literal in 'lits' is True.

    Clauses: 1 clause (lits[0] v lits[1] v ... v lits[k-1]).
    Auxiliary variables: 0.
    """
    if not lits:
        return []
    return [list(lits)]


def encode_amo_pairwise(lits: List[int], aux_mgr: AuxVarManager) -> List[List[int]]:
    """Pairwise (Naive) At-Most-One Encoding.

    For every pair (u, v), adds clause (~u v ~v).
    Auxiliary variables: 0.
    Clauses: k*(k-1)/2.
    """
    clauses: List[List[int]] = []
    k = len(lits)
    if k <= 1:
        return clauses

    for i in range(k):
        for j in range(i + 1, k):
            clauses.append([-lits[i], -lits[j]])
    return clauses


def encode_amo_sequential_counter(lits: List[int], aux_mgr: AuxVarManager) -> List[List[int]]:
    """Sequential Counter At-Most-One Encoding (Sinz, 2005).

    Introduces k-1 auxiliary variables s_1, ..., s_{k-1}.
    Clauses:
      (~x_1 v s_1)
      (~s_{i-1} v s_i)       for i = 2..k-1
      (~x_i v s_i)           for i = 2..k-1
      (~x_i v ~s_{i-1})      for i = 2..k
    Auxiliary variables: k - 1.
    Clauses: 3k - 4 (for k >= 2).
    Arc-consistent.
    """
    clauses: List[List[int]] = []
    k = len(lits)
    if k <= 1:
        return clauses

    s = aux_mgr.allocate(k - 1)  # s[0]..s[k-2] corresponds to s_1..s_{k-1}

    # (~x_1 v s_1)
    clauses.append([-lits[0], s[0]])

    # For i = 2..k-1 (0-indexed: i=1..k-2)
    for i in range(1, k - 1):
        # (~s_{i-1} v s_i)
        clauses.append([-s[i - 1], s[i]])
        # (~x_i v s_i)
        clauses.append([-lits[i], s[i]])
        # (~x_i v ~s_{i-1})
        clauses.append([-lits[i], -s[i - 1]])

    # For i = k (0-indexed: i=k-1)
    # (~x_k v ~s_{k-1})
    clauses.append([-lits[k - 1], -s[k - 2]])

    return clauses


def encode_amo_commander(lits: List[int], aux_mgr: AuxVarManager, group_size: int = 3) -> List[List[int]]:
    r"""Commander Variable At-Most-One Encoding (Klieber & Kwon, 2007).

    Partitions literals into disjoint groups of size <= group_size.
    For each group, a commander variable c represents whether any variable in the group is True.
    - At most one variable in the group can be True (pairwise within group).
    - If any variable in group is True -> commander is True: (~x v c) for all x in group.
    - If commander is True -> at least one variable is True: (~c v \/ x in group).
    - Exactly one commander among all groups is True (or AMO recursively).
    """
    clauses: List[List[int]] = []
    k = len(lits)
    if k <= 1:
        return clauses

    if k <= group_size:
        return encode_amo_pairwise(lits, aux_mgr)

    # Partition into groups
    groups = [lits[i:i + group_size] for i in range(0, k, group_size)]
    commanders: List[int] = []

    for group in groups:
        if len(group) == 1:
            commanders.append(group[0])
            continue

        c = aux_mgr.allocate_one()
        commanders.append(c)

        # Pairwise AMO within group
        clauses.extend(encode_amo_pairwise(group, aux_mgr))

        # group -> c: (~x v c) for each x
        for x in group:
            clauses.append([-x, c])

        # c -> ALO(group): (~c v x_1 v x_2 v ...)
        clauses.append([-c] + list(group))

    # Recursively enforce AMO on the commander variables
    clauses.extend(encode_amo_commander(commanders, aux_mgr, group_size))
    return clauses


def encode_amo_product(lits: List[int], aux_mgr: AuxVarManager) -> List[List[int]]:
    """Product At-Most-One Encoding (Chen, 2010).

    Arranges k literals in a 2D grid of size p x q >= k,
    with p = ceil(sqrt(k)), q = ceil(k / p).
    Introduces p row variables u_1..u_p and q col variables v_1..v_q.
    For literal at cell (r, c):
      (~x v u_r)
      (~x v v_c)
    Enforces AMO(u) and AMO(v) using pairwise.
    Auxiliary variables: p + q = O(sqrt(k)).
    Clauses: 2k + p(p-1)/2 + q(q-1)/2 = O(k).
    """
    clauses: List[List[int]] = []
    k = len(lits)
    if k <= 1:
        return clauses
    if k <= 3:
        # For small k, pairwise is more compact than product
        return encode_amo_pairwise(lits, aux_mgr)

    p = int(math.ceil(math.sqrt(k)))
    q = int(math.ceil(k / p))

    u = aux_mgr.allocate(p)
    v = aux_mgr.allocate(q)

    for idx, lit in enumerate(lits):
        r = idx // q
        c = idx % q
        clauses.append([-lit, u[r]])
        clauses.append([-lit, v[c]])

    # AMO on row variables u
    clauses.extend(encode_amo_pairwise(u, aux_mgr))
    # AMO on col variables v
    clauses.extend(encode_amo_pairwise(v, aux_mgr))

    return clauses


def encode_amo_binary(lits: List[int], aux_mgr: AuxVarManager) -> List[List[int]]:
    """Binary / Bitwise At-Most-One Encoding (Frisch et al., 2005).

    Uses m = ceil(log2(k)) auxiliary variables b_0..b_{m-1}.
    Each literal x_i (0 <= i < k) maps to the binary representation of i.
    For each bit position j (0 <= j < m):
      If j-th bit of i is 1: (~x_i v b_j)
      If j-th bit of i is 0: (~x_i v ~b_j)
    If two literals x_i and x_j are both True, they conflict on at least one bit.
    Auxiliary variables: ceil(log2(k)).
    Clauses: k * ceil(log2(k)).
    """
    clauses: List[List[int]] = []
    k = len(lits)
    if k <= 1:
        return clauses

    m = int(math.ceil(math.log2(k)))
    b = aux_mgr.allocate(m)

    for i, lit in enumerate(lits):
        for bit in range(m):
            if (i >> bit) & 1:
                clauses.append([-lit, b[bit]])
            else:
                clauses.append([-lit, -b[bit]])

    return clauses


# Registry of available AMO encodings
AMO_ENCODINGS: Dict[str, Callable[[List[int], AuxVarManager], List[List[int]]]] = {
    "pairwise": encode_amo_pairwise,
    "seqcounter": encode_amo_sequential_counter,
    "commander": encode_amo_commander,
    "product": encode_amo_product,
    "binary": encode_amo_binary,
}


def cell_to_var(r: int, c: int, n: int) -> int:
    """Map chessboard row r and column c (0-indexed) to 1-based DIMACS variable."""
    return r * n + c + 1


def var_to_cell(var_id: int, n: int) -> Tuple[int, int]:
    """Map 1-based DIMACS variable back to (row, column) in 0-indexed coordinates."""
    idx = var_id - 1
    return idx // n, idx % n


def build_nqueens_cnf(n: int, encoding_name: str = "pairwise") -> CNFFormula:
    """Build CNF formula for N-Queens using the specified AMO encoding.

    Constraints:
    1. Row constraints: Exactly-One queen per row:
       - At-Least-One (ALO): (x_r,0 v x_r,1 v ... v x_r,n-1)
       - At-Most-One (AMO): using the chosen AMO strategy
    2. Column constraints: Exactly-One queen per column:
       - At-Least-One (ALO): (x_0,c v x_1,c v ... v x_n-1,c)
       - At-Most-One (AMO): using the chosen AMO strategy
    3. Main diagonals (r - c = const): At-Most-One queen per diagonal (len >= 2).
    4. Anti diagonals (r + c = const): At-Most-One queen per anti-diagonal (len >= 2).

    Args:
        n: Board dimension.
        encoding_name: One of 'pairwise', 'seqcounter', 'commander', 'product', 'binary'.

    Returns:
        CNFFormula object with full clause list and metadata.
    """
    if encoding_name not in AMO_ENCODINGS:
        raise ValueError(
            f"Unknown encoding '{encoding_name}'. Available: {list(AMO_ENCODINGS.keys())}"
        )

    t_start = time.perf_counter()
    num_primary_vars = n * n
    aux_mgr = AuxVarManager(start_id=num_primary_vars + 1)
    amo_func = AMO_ENCODINGS[encoding_name]
    clauses: List[List[int]] = []

    # 1. Row constraints (Exactly-One)
    for r in range(n):
        row_lits = [cell_to_var(r, c, n) for c in range(n)]
        # ALO
        clauses.extend(encode_alo(row_lits))
        # AMO
        clauses.extend(amo_func(row_lits, aux_mgr))

    # 2. Column constraints (Exactly-One)
    for c in range(n):
        col_lits = [cell_to_var(r, c, n) for r in range(n)]
        # ALO
        clauses.extend(encode_alo(col_lits))
        # AMO
        clauses.extend(amo_func(col_lits, aux_mgr))

    # 3. Main Diagonals: r - c = d, where d in [-(n-2) .. (n-2)]
    # Diagonal length must be >= 2
    for d in range(-(n - 2), n - 1):
        diag_lits = [
            cell_to_var(r, r - d, n)
            for r in range(n)
            if 0 <= r - d < n
        ]
        if len(diag_lits) >= 2:
            clauses.extend(amo_func(diag_lits, aux_mgr))

    # 4. Anti Diagonals: r + c = s, where s in [1 .. 2n-3]
    for s in range(1, 2 * n - 2):
        anti_lits = [
            cell_to_var(r, s - r, n)
            for r in range(n)
            if 0 <= s - r < n
        ]
        if len(anti_lits) >= 2:
            clauses.extend(amo_func(anti_lits, aux_mgr))

    t_end = time.perf_counter()

    return CNFFormula(
        n=n,
        encoding_name=encoding_name,
        num_primary_vars=num_primary_vars,
        num_aux_vars=aux_mgr.count,
        clauses=clauses,
        build_time_seconds=t_end - t_start
    )
