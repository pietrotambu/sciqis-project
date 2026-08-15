"""
Check that the frameworks agree before any timing is compared.
"""

import argparse
import itertools
import pathlib
import sys

import numpy as np

TOL = 1e-9


def main():
    p = argparse.ArgumentParser(description="Compare saved statevectors across frameworks.")
    p.add_argument("-c", "--circuit", default="ghz", choices=["ghz", "random", "qft"])
    p.add_argument("-n", "--nqubits", type=int, required=True)
    p.add_argument("--results", default="results")
    args = p.parse_args()

    pattern = f"state_*_{args.circuit}_n{args.nqubits}.npy"
    files = sorted(pathlib.Path(args.results).glob(pattern))
    if len(files) < 2:
        sys.exit(f"need at least 2 statevectors matching {pattern}, found {len(files)}")

    # state_<framework>_<circuit>_n<N>.npy
    states = {f.name.split("_")[1]: np.load(f) for f in files}

    print(f"{args.circuit}  n={args.nqubits}  ({len(states)} frameworks)")
    ok = True
    for (name_a, a), (name_b, b) in itertools.combinations(states.items(), 2):
        # |<a|b>| rather than element-wise equality: simulators are free to
        # differ by a global phase, and that is not a disagreement.
        overlap = abs(np.vdot(a, b)) / (np.linalg.norm(a) * np.linalg.norm(b))
        good = abs(overlap - 1.0) < TOL
        ok &= good
        print(f"  {name_a:<10} vs {name_b:<10} |<a|b>| = {overlap:.12f}  {'OK' if good else 'MISMATCH'}")

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
