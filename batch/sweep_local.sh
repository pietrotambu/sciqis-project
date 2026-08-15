#!/bin/bash
# Local CPU sweep: every framework over the same qubit range, no per-framework
# caps. Usage: ./batch/sweep_local.sh          (results land in results/)

set -u
cd "$(dirname "$0")/.." || exit 1

FRAMEWORKS="qiskit pennylane qulacs cirq braket"
CIRCUITS="ghz random qft"
QUBITS="4 6 8 10 12 14 16 18 20 22 24 26"

# n is the OUTER loop so that stopping early still leaves a complete
# cross-framework comparison up to whatever n was reached, rather than some
# frameworks finished and others missing entirely.
mkdir -p results
for n in $QUBITS; do
    for c in $CIRCUITS; do
        for fw in $FRAMEWORKS; do
            echo "== n=$n $c $fw"
            # The slow NumPy engines blow up on the biggest circuits; cap each
            # run so one of them cannot stall the whole sweep.
            timeout 1200 uv run src/main.py -f "$fw" -c "$c" -n "$n" --reps 3 \
                > /dev/null || echo "   SKIPPED (failed or over 20 min)"
        done
    done
    # Refresh tables and plots after each n, so results are usable while it runs.
    uv run src/report.py --plot > /dev/null
done

uv run src/report.py --plot
echo "done"
