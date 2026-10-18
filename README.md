# N-Queens Solver: SAT, Gurobi MIP, CP-SAT, and CPLEX

**Term Project – Modern Topics in Computer Science, Academic Year 2026–2027**

**Topic:** SAT-Based Solving for the N-Queens Problem: Encoding Strategies and Performance Comparison with Gurobi MIP and CP-SAT

---

## 📋 Project Overview

This project implements and benchmarks **exact solving** of the classical N-Queens problem across four solver paradigms:

| Paradigm | Tools | Status |
|---|---|---|
| **SAT Solving** | PySAT (Glucose 4, CaDiCaL, MiniSat 2.2, Lingeling, MergeSat 3) | ✅ Full |
| **Mixed-Integer Programming** | Gurobi 13.0.3 (restricted academic license) | ✅ Up to N=44 |
| **Constraint Programming (CP-SAT)** | Google OR-Tools 9.15 | ✅ Up to N=500+ |
| **IBM CPLEX MIP & CP** | CPLEX 22.2 Community Edition | ✅ Up to N=31 (MIP), N=500+ (CP Optimizer) |

Five SAT **cardinality encodings** are implemented and compared:
- **Pairwise** (naive, 0 aux vars, O(k²) clauses)
- **Sequential Counter** (Sinz, 2005 – O(k) clauses, arc-consistent)
- **Commander Variable** (Klieber & Kwon, 2007 – O(k) clauses)
- **Product Encoding** (Chen, 2010 – O(√k) aux vars)
- **Binary/Bitwise Encoding** (Frisch et al., 2005 – O(log k) aux vars)

---

## 🗂️ Repository Structure

```
BTL_01/
├── src/nqueens/
│   ├── model.py            # Data structures: BoardSolution, SolverResult, SolverStatus
│   ├── encodings.py        # 5 AMO/ALO/EO cardinality encodings + CNF builder
│   ├── validation.py       # Independent solution validator (no constraint reuse)
│   ├── sat_solver.py       # PySAT integration with timer interrupt
│   ├── gurobi_solver.py    # Gurobi MIP with WLS credential support
│   ├── cp_sat_solver.py    # OR-Tools CP-SAT (AllDifferent + Boolean 2D)
│   ├── cplex_solver.py     # IBM CPLEX MIP + CP Optimizer
│   ├── experiment.py       # Benchmark orchestrator (Experiments A–E)
│   └── reporting.py        # Statistical analysis + LaTeX table export
├── scripts/
│   ├── run_correctness_tests.py   # Comprehensive cross-solver correctness suite
│   ├── run_benchmarks.py          # Full/Quick benchmark runner
│   ├── generate_plots.py          # Publication-quality figure generator
│   └── compile_paper.py           # LaTeX paper compilation script
├── tests/                         # pytest unit tests (45 tests, all passing)
├── results/
│   ├── raw/               # Real benchmark CSVs (Experiments A–E)
│   └── figures/           # PDF + PNG publication figures
├── paper/
│   ├── main.tex           # Elsevier cas-sc scientific report
│   ├── references.bib     # Verified bibliography (no fabricated references)
│   ├── cas-sc.cls         # Official Elsevier CAS template
│   └── figs/              # Figures embedded in the paper
├── requirements.txt
├── pytest.ini
└── .gitignore
```

---

## ⚙️ Requirements

- **Python 3.10+** (tested on 3.13.15)
- **OS:** Windows 10/11 or Linux

### Install Dependencies

```bash
pip install python-sat ortools gurobipy cplex docplex matplotlib pandas numpy scipy pytest psutil
```

Or from requirements file:

```bash
pip install -r requirements.txt
```

### Solver Versions Used
| Library | Version |
|---|---|
| python-sat (PySAT) | 1.9.dev16 |
| ortools | 9.15.6755 |
| gurobipy | 13.0.3 |
| cplex | 22.2.0.1 |
| docplex | 2.32.264 |
| matplotlib | 3.11.2 |
| pandas | 3.0.6 |
| numpy | 2.5.4 |
| scipy | 1.18.1 |

---

## 🔑 Gurobi WLS Configuration (Academic License)

> ⚠️ **NEVER** put Gurobi credentials in source code, logs, or this repository.

If you have a Gurobi WLS (Web License Service) Academic Compute Server license, configure it via **environment variables** before running:

```powershell
# PowerShell (Windows)
$env:GRB_WLSACCESSID = "your-access-id-here"
$env:GRB_WLSSECRET   = "your-secret-here"
$env:GRB_LICENSEID   = "your-license-id-number"
```

```bash
# Bash (Linux/macOS)
export GRB_WLSACCESSID="your-access-id-here"
export GRB_WLSSECRET="your-secret-here"
export GRB_LICENSEID="your-license-id-number"
```

Without WLS credentials, Gurobi runs in restricted mode (capped at **2,000 binary variables**, i.e., N ≤ 44 for N-Queens).  
Instances exceeding the limit are recorded as `LICENSE_LIMIT` — not fabricated data.

---

## 🧪 Running Tests

Run the full automated test suite (45 tests):

```bash
pytest tests/
```

Run cross-solver correctness checks (N=1 to N=16 across all solvers):

```bash
python scripts/run_correctness_tests.py
```

---

## 🚀 Running Solvers Individually

```python
from src.nqueens.sat_solver import solve_nqueens_sat
from src.nqueens.gurobi_solver import solve_nqueens_gurobi
from src.nqueens.cp_sat_solver import solve_nqueens_cp_sat

# PySAT with Sequential Counter encoding
result = solve_nqueens_sat(n=32, encoding="seqcounter", solver_name="glucose4")
print(result.status, result.solve_time_seconds, result.solution_valid)

# Gurobi MIP
result = solve_nqueens_gurobi(n=32, timeout_seconds=60)
print(result.status, result.total_time_seconds)

# OR-Tools CP-SAT
result = solve_nqueens_cp_sat(n=200, formulation="alldifferent")
print(result.status, result.total_time_seconds)
```

---

## 📊 Running Benchmarks

### Quick mode (for smoke testing, ~10 minutes):
```bash
python scripts/run_benchmarks.py --mode quick
```

### Full publication benchmarks (Experiments A–E, may take 2+ hours):
```bash
python scripts/run_benchmarks.py --mode full
```

Raw CSV data is saved to `results/raw/`.

---

## 📈 Generating Figures

After running benchmarks:

```bash
python scripts/generate_plots.py
```

Produces 7 publication-quality PDF + PNG figures in `results/figures/` and `paper/figs/`.

---

## 📄 Compiling the LaTeX Paper

### Prerequisites
MiKTeX or TeX Live must be installed with the Elsevier CAS bundle packages.

```bash
python scripts/compile_paper.py
```

Or manually:

```bash
cd paper
pdflatex -enable-installer -interaction=nonstopmode main.tex
bibtex main
pdflatex -enable-installer -interaction=nonstopmode main.tex
pdflatex -enable-installer -interaction=nonstopmode main.tex
```

Output: `paper/main.pdf`

---

## 🔬 Reproducibility

All experiments were run on:
- **CPU:** AMD Ryzen 5 7535HS (6 physical cores, 12 logical threads)
- **RAM:** 16 GB DDR5
- **OS:** Windows 11 Home 64-bit
- **Python:** 3.13.15

To fully replicate results:

1. Install the exact library versions in `requirements.txt`
2. Configure Gurobi WLS (if available)
3. Run `python scripts/run_benchmarks.py --mode full`
4. Run `python scripts/generate_plots.py`
5. Compile `paper/main.tex`

---

## 📌 Known Limitations

| Issue | Detail |
|---|---|
| **Gurobi license limit** | Restricted academic mode: N ≤ 44 (2,000 variable ceiling) |
| **CPLEX Community Edition** | N ≤ 31 for MIP (1,000 variable limit); CP Optimizer unlimited |
| **SAT scalability** | Pairwise encoding: N ≥ 100 requires >1.6M clauses → slow build |
| **MiKTeX package installation** | Some CAS template packages require MiKTeX auto-install (needs network) |

---

## 📚 References

Key references (full list in `paper/references.bib`):
- Sinz, C. (2005). Towards an Optimal CNF Encoding of Boolean Cardinality Constraints. *CP 2005*.
- Klieber, W. & Kwon, G. (2007). Efficient CNF Encoding for Selecting 1 from N Objects.
- Ignatiev, A. et al. (2018). PySAT: A Python Toolkit for Prototyping with SAT Oracles. *SAT 2018*.
- Audemard, G. & Simon, L. (2018). On the Glucose SAT Solver. *IJAIT*.
- Régin, J.-C. (1994). A filtering algorithm for constraints of difference in CSPs. *AAAI-94*.
- Biere, A. et al. (eds., 2021). *Handbook of Satisfiability*, 2nd ed. IOS Press.

---

## 📝 License

This project is submitted as an individual term assignment for **Modern Topics in Computer Science** at the Faculty of Computer Science and Engineering.  
All solver tools are used under their respective academic/community licenses.
