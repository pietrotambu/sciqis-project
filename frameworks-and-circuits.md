# Frameworks and circuits to use

Notes to myself on what to pick for the comparison. Goal: small project, few moving parts.

## Frameworks

**Constraint: Python only.** All four below are plain `uv add` packages with a Python API — the C++/CUDA lives inside the wheel, I never compile or write any of it. Nothing here needs a non-Python toolchain.

**Constraint: complex128 everywhere.** Every framework must run in double precision, so that no part of a timing gap is just "moved half the bytes". A framework that cannot do complex128 is not used.

Four frameworks, all statevector, so the comparison is apples-to-apples.

| Framework | Org | Device string | Backend | Why |
|---|---|---|---|---|
| **Qiskit + Aer** | IBM | `AerSimulator(device="CPU")` / `device="GPU"` | C++, OpenMP / cuStateVec | Same API on CPU and GPU → the CPU/GPU crossover point comes out of one code path. Main workhorse. |
| **PennyLane Lightning** | Xanadu | `lightning.qubit` / `lightning.gpu` | C++ / cuQuantum | Independent fast implementation, also has both devices. Good second opinion. |
| **Cirq** | Google | `cirq.Simulator()` | pure Python + NumPy | Slow baseline. Makes the "why is it different" discussion easy: no C++ kernel, gates applied as tensor contractions. |
| **Braket local** | AWS | `LocalSimulator("braket_sv")` | pure Python + NumPy | Second pure-NumPy point, from a different vendor. Confirms the slow group is about *method*, not about one bad implementation. No GPU, no thread control. |
| **Qulacs** | Osaka U / QunaSys | `QuantumState` + `QuantumCircuit` | C++, OpenMP | The speed reference. Smallest memory footprint by a wide margin (46 MB vs 156–290 MB at n=18). Little-endian like Qiskit, so no reordering. |

Rejected, with reasons worth stating in the report:
- **qsim** (Google's fast engine) — single precision only. Precision is a compile-time template parameter in qsim and `QSimOptions` has no precision field, so complex128 is impossible without a source build. Ruled out by the precision constraint. Google is still represented by Cirq.
- **ProjectQ** — fails to build even with a compiler present: `AttributeError: 'Compiler' object has no attribute 'dry_run'`, a setuptools incompatibility. Last release 2022, effectively dead on Python 3.12.
- **QuEST** — `pyquest-cffi` is source-only (needs a compiler). The `pyquest` wheel is genuine Cython QuEST bindings but is built against NumPy 1.x and raises `numpy.dtype size changed` on import under NumPy 2.x. Fixing it would mean pinning the whole project to NumPy 1.x, which would affect every other framework.
- **Yao.jl** — *technically works*: `pip install juliacall` pulls a Julia runtime automatically, Yao loads, GHZ verifies at complex128. Rejected on cost, not capability: ~1.7 GB of Julia runtime and packages, needs network access to bootstrap, JIT warm-up on first call, and `~/.julia` would eat the HPC home quota. Not worth it for one more data point.
- **cuQuantum (NVIDIA)** — not a competing simulator but the GPU engine that Aer-GPU and Lightning-GPU both call. Benchmarking it separately would measure the same C++ twice.
- **Stim** — Clifford only, cannot express QFT's phase rotations.

Install notes:
- `qiskit-aer-gpu` is a separate wheel, CUDA 12, Linux x86 only → install it only in the GPU env on the HPC. Kept in the `gpu` dependency group so `uv sync` works on my laptop.
- `pennylane-lightning-gpu` needs cuQuantum, same story.
- Python is pinned to 3.12 (`requires-python = ">=3.11,<3.13"`): compiled wheels lag new Python releases, and building from source would break the Python-only constraint.

Gotchas that will bite:
- **Qubit ordering**: Qiskit and Qulacs are little-endian; Cirq, PennyLane and Braket are big-endian. Verified by hand, not taken from the docs. Each file reverses on save so `verify.py` stays framework-agnostic.
- **Rotation sign**: Qulacs defines `RX(t) = exp(+i t X/2)`; everyone else uses `exp(-i t X/2)`. The angles are negated in `bench_qulacs.py`. Without this it silently simulates a *different circuit* — the timings would look perfectly reasonable and be meaningless. This is exactly what `verify.py` is for.
- **Global phase**: compare with `|<psi_a|psi_b>| ≈ 1`, not element-wise equality.
- **Threading**: check each engine actually uses all cores. A single-threaded default silently turns a fair comparison into an unfair one.

## Circuits

Three circuits. **`n` is the only knob** — each circuit's depth follows from `n`, so there is one axis to sweep and one axis to explain. Each framework file implements all three in its own syntax.

1. **GHZ(n)** — `H` on q0, then a chain of `CNOT`s.
   - Depth grows as `O(n)`, one gate per qubit. Cheapest circuit.
   - Exact state is known (`(|0..0> + |1..1>)/sqrt(2)`) → this is the circuit I use to *verify* the frameworks agree before timing anything.
   - Fully entangled, so no simulator can cheat by factorising.

2. **Layered random circuit (brickwork)** — per layer: `RX` then `RZ` on every qubit, then `CZ` on alternating even/odd neighbour pairs.
   - **Square circuit: depth = n.** That is the standard convention for random-circuit benchmarking (it's what Quantum Volume uses), and it keeps `n` as the only knob.
   - Main timing circuit. Gate mix is realistic (1q + 2q).
   - Fixed RNG seed, and only `RX`/`RZ`/`CZ` — gates whose definitions are identical in all three frameworks, so no `U3`/`Rot` convention mismatches.

3. **QFT(n)** — `H` + controlled phase ladder + final swaps.
   - Structured, `O(n^2)` gates, many two-qubit *controlled-phase* gates.
   - Stress test for how each framework applies parameterised controlled gates, and it produces a dense output state.

Optional 4th, useful for the write-up: **single-qubit-only circuit** (d layers of rotations, no entangling gates). It stays a product state, so it isolates pure gate-application overhead and shows which frameworks special-case 1q gates.

## Sizes to sweep

Statevector memory is `2^n * 16 bytes` (complex128):

| n | memory |
|---|---|
| 20 | 17 MB |
| 25 | 537 MB |
| 28 | 4.3 GB |
| 30 | 17 GB |
| 32 | 69 GB |

- CPU sweep: `n = 4..28` (stop where the node's RAM or the wall time runs out). Cirq is capped lower, it falls off a cliff first.
- GPU sweep: same range; ceiling is VRAM, so probably `n <= 30` on one card in complex64.

**Expected scaling** — memory is pure `2^n`, but runtime also carries the gate count, so it is not:

| Circuit | Gates | Runtime |
|---|---|---|
| GHZ | `n` | `n · 2^n` |
| random (d = n) | `2.5 n^2` | `n^2 · 2^n` |
| QFT | `~n^2/2` | `n^2 · 2^n` |

Worth saying out loud in the write-up: fitting runtime against a plain `2^n` will look wrong, and that is expected. Since random and QFT have the *same* scaling, any timing gap between them is about gate *type* (RX/RZ/CZ vs controlled-phase), not gate count.

## What to record per run

One JSON line per (framework, device, circuit, n): `build_s` and `run_s` kept
separate (Qiskit's transpile is a fixed ~40 ms that has nothing to do with
simulation speed — lumping it in makes Qiskit look bad at small `n`), best of
`--reps` with a warm-up discarded, `n_gates`, peak RSS, precision, versions,
hostname. Appends to `results/<framework>_<device>.jsonl` → plotting is just a concat.

Agreement is checked separately by `verify.py` on saved `.npy` statevectors, and it
exits non-zero on a mismatch.
