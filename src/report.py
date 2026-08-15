"""
Tables and plots from results/*.jsonl
"""

import argparse
import glob
import json
import os


def load(results):
    rows = []
    for path in glob.glob(os.path.join(results, "*.jsonl")):
        with open(path) as fh:
            rows += [json.loads(line) for line in fh if line.strip()]
    return rows


def table(rows, circuit, field, unit, scale=1):
    sel = [r for r in rows if r["circuit"] == circuit]
    frameworks = sorted({r["framework"] for r in sel})
    best = {}
    for r in sel:  # keep the fastest run per (framework, n) if a sweep was re-run
        key = (r["framework"], r["nqubits"])
        if key not in best or r["run_s"] < best[key]["run_s"]:
            best[key] = r

    print(f"\n{circuit} - {unit}")
    print("   n  " + "".join(f"{f:>12}" for f in frameworks))
    for n in sorted({r["nqubits"] for r in sel}):
        cells = ""
        for f in frameworks:
            r = best.get((f, n))
            cells += f"{r[field] * scale:12.2f}" if r else f"{'-':>12}"
        print(f"{n:4d}  {cells}")


def plot(rows, results):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    for circuit in sorted({r["circuit"] for r in rows}):
        sel = [r for r in rows if r["circuit"] == circuit]
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
        for f in sorted({r["framework"] for r in sel}):
            pts = sorted((r["nqubits"], r["run_s"], r["peak_rss_mb"])
                         for r in sel if r["framework"] == f)
            ax1.plot([p[0] for p in pts], [p[1] * 1000 for p in pts], "o-", label=f)
            ax2.plot([p[0] for p in pts], [p[2] for p in pts], "o-", label=f)
        for ax, ylab in ((ax1, "run time [ms]"), (ax2, "peak memory [MB]")):
            ax.set_yscale("log")
            ax.set_xlabel("qubits")
            ax.set_ylabel(ylab)
            ax.grid(alpha=0.3)
        ax1.set_title(circuit)
        ax2.set_title(circuit)
        ax1.legend(fontsize=8)
        fig.tight_layout()
        out = os.path.join(results, f"scaling_{circuit}.png")
        fig.savefig(out, dpi=120)
        plt.close(fig)
        print(f"wrote {out}")


def main():
    p = argparse.ArgumentParser(description="summarise benchmark results")
    p.add_argument("--results", default="results")
    p.add_argument("--plot", action="store_true")
    args = p.parse_args()

    rows = load(args.results)
    if not rows:
        raise SystemExit(f"no .jsonl files found in {args.results}/")
    print(f"{len(rows)} runs")

    for circuit in sorted({r["circuit"] for r in rows}):
        table(rows, circuit, "run_s", "run time [ms]", scale=1000)
    for circuit in sorted({r["circuit"] for r in rows}):
        table(rows, circuit, "peak_rss_mb", "peak memory [MB]")

    if args.plot:
        plot(rows, args.results)


if __name__ == "__main__":
    main()
