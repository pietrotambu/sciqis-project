"""
Benchmark entrypoint
"""

import argparse
import importlib.metadata
import json
import os
import resource
import timeit

# Single-threaded, always.
for _var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
             "NUMEXPR_NUM_THREADS", "QULACS_NUM_THREADS", "RAYON_NUM_THREADS"):
    os.environ[_var] = "1"


# All possible frameworks, and the pip package whose version we record.
FRAMEWORKS = {
    "qiskit": "qiskit",
    "pennylane": "pennylane",
    "cirq": "cirq-core",
    "braket": "amazon-braket-sdk",
    "qulacs": "qulacs",
}


def rss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def measure(fn, reps):
    """Per-call times, the way %timeit does it: autorange picks a loop count so
    fast calls are still measured accurately, then repeat that many times."""
    loops, _ = timeit.Timer(fn).autorange()
    return [t / loops for t in timeit.Timer(fn).repeat(repeat=reps, number=loops)]


def main():
    p = argparse.ArgumentParser(description="statevector benchmark")
    p.add_argument("-f", "--framework", required=True, choices=FRAMEWORKS)
    p.add_argument("-c", "--circuit", default="ghz", choices=["ghz", "random", "qft"])
    p.add_argument("-n", "--nqubits", type=int, required=True)
    p.add_argument("--reps", type=int, default=3)
    p.add_argument("--device", default="cpu", choices=["cpu", "gpu"])
    p.add_argument("--results", default="results")
    p.add_argument("--out", default=None)
    args = p.parse_args()

    backend = importlib.import_module(f"frameworks.{args.framework}")
    # Whatever it costs to get the libraries loaded, before any circuit exists.
    # Subtracting this from the peak isolates what the simulation itself costs.
    baseline_rss = rss_mb()

    os.makedirs(args.results, exist_ok=True)
    build, run, n_gates = backend.prepare(
        args.circuit, args.nqubits, args.device
    )

    run()  # warm-up
    build_times = measure(build, args.reps)
    run_times = measure(run, args.reps)

    record = {
        "framework": backend.FRAMEWORK,
        "version": importlib.metadata.version(FRAMEWORKS[args.framework]),
        "device": args.device,
        "circuit": args.circuit,
        "nqubits": args.nqubits,
        "n_gates": n_gates,
        "build_s": min(build_times),
        "run_s": min(run_times),
        "peak_rss_mb": rss_mb(),                   # whole process
        "sim_rss_mb": rss_mb() - baseline_rss,     # minus the cost of the imports
    }

    out = args.out or os.path.join(
        args.results, f"{backend.FRAMEWORK}_{args.device}.jsonl"
    )
    with open(out, "a") as fh:
        fh.write(json.dumps(record) + "\n")
    print(json.dumps(record))


if __name__ == "__main__":
    main()
