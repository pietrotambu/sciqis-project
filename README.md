# SCIQIS 10387 — Comparing quantum computing simulators

This project times **5 quantum simulators** (Qiskit-Aer, PennyLane-Lightning,
Cirq, Braket, Qulacs) on **3 circuits** (GHZ, random, QFT), from 4 to 30
qubits, on a CPU and on an NVIDIA A100 GPU.

---

## Requirements

- **uv** - install this yourself, it's the only
  tool you need
- **Python 3.12** - uv downloads it for you automatically
- Any OS (Linux, macOS, Windows) for the CPU runs. The GPU runs only work on
  Linux with an NVIDIA GPU + CUDA.


## Setup

Sync the dependencies with uv:

```bash
uv sync

## Or
make sync
```

This creates a `.venv` folder with everything installed, using the exact
versions in `uv.lock`.

If you also want the GPU packages (Linux + CUDA only), install them into a
separate environment so your normal CPU environment stays clean:

```bash
UV_PROJECT_ENVIRONMENT=.venv-gpu uv sync --group gpu

## Or
make sync-gpu
```

## Running a benchmark

```bash
uv run src/main.py -f qiskit -c ghz -n 20

## Or
make run FW=qiskit CIRCUIT=ghz N=20
```

This runs one simulation and prints one line of results. The same line is
also saved to `results/<framework>_<device>.jsonl`.

### Options

| Flag | Values | Default | What it means |
|---|---|---|---|
| `-f` | `qiskit` `pennylane` `cirq` `braket` `qulacs` | *required* | Which simulator to use |
| `-c` | `ghz` `random` `qft` | `ghz` | Which circuit to run |
| `-n` | integer | *required* | Number of qubits |
| `--reps` | integer | `3` | How many times to repeat the timing (keeps the fastest) |
| `--device` | `cpu` `gpu` | `cpu` | Only Qiskit and PennyLane support `gpu` |

### More examples

```bash
# Run the random circuit at 24 qubits
uv run src/main.py -f pennylane -c random -n 24
## Or
make run FW=pennylane CIRCUIT=random N=24


# Run QFT on the GPU (needs the .venv-gpu environment `make sync-gpu`)
UV_PROJECT_ENVIRONMENT=.venv-gpu uv run src/main.py -f qiskit -c qft -n 26 --device gpu
```

## Running the jobs on the DTU HPC

```bash
bsub < batch/sciqis_cpu.sub     # all 5 frameworks, CPU
bsub < batch/sciqis_gpu.sub     # qiskit + pennylane, GPU
```

Logs are written to `logs/`, results are appended to `results/`.

---

## Makefile shortcuts

On Unix-like OS, run `make help` or just `make` to see all the available commands