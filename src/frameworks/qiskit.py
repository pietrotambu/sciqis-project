"""
Qiskit Aer backend
"""

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

FRAMEWORK = "qiskit"
SEED = 1234


def ghz(n):
    qc = QuantumCircuit(n)
    qc.h(0)
    for q in range(n - 1):
        qc.cx(q, q + 1)
    return qc


def random(n):
    # Square circuit: depth == width
    # benchmarking. Same seed, same draw order and same gate set in every
    # framework, so all of them build the identical circuit.
    angles = np.random.default_rng(SEED).uniform(0, 2 * np.pi, size=(n, n, 2))
    qc = QuantumCircuit(n)
    for layer in range(n):
        for q in range(n):
            qc.rx(angles[layer, q, 0], q)
            qc.rz(angles[layer, q, 1], q)
        for q in range(layer % 2, n - 1, 2):
            qc.cz(q, q + 1)
    return qc


def qft(n):
    qc = QuantumCircuit(n)
    for j in range(n):
        qc.h(j)
        for k in range(j + 1, n):
            qc.cp(np.pi / 2 ** (k - j), k, j)
    for j in range(n // 2):
        qc.swap(j, n - 1 - j)
    return qc


CIRCUITS = {"ghz": ghz, "random": random, "qft": qft}


def prepare(circuit, n, device):
    sim = AerSimulator(
        method="statevector",
        device=device.upper(),
        precision="double",  # this means complex128
        max_parallel_threads=1,
    )

    def build():
        qc = CIRCUITS[circuit](n)
        qc.save_statevector()
        return transpile(qc, sim)

    transpiled = build()

    def run():
        return sim.run(transpiled).result()

    return build, run, CIRCUITS[circuit](n).size()
