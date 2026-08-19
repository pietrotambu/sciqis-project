"""
Cirq backend - pure NumPy reference, CPU only
"""

import cirq
import numpy as np

FRAMEWORK = "cirq"
SEED = 1234


def ghz(q):
    yield cirq.H(q[0])
    for i in range(len(q) - 1):
        yield cirq.CNOT(q[i], q[i + 1])


def random(q):
    # Square circuit: depth == width
    # benchmarking. Same seed, same draw order and same gate set in every
    # framework, so all of them build the identical circuit.
    n = len(q)
    angles = np.random.default_rng(SEED).uniform(0, 2 * np.pi, size=(n, n, 2))
    for layer in range(n):
        for i in range(n):
            yield cirq.rx(angles[layer, i, 0])(q[i])
            yield cirq.rz(angles[layer, i, 1])(q[i])
        for i in range(layer % 2, n - 1, 2):
            yield cirq.CZ(q[i], q[i + 1])


def qft(q):
    n = len(q)
    for j in range(n):
        yield cirq.H(q[j])
        for k in range(j + 1, n):
            # CZPowGate(exponent=t) is diag(1,1,1,exp(i*pi*t)), so t = theta/pi.
            yield cirq.CZPowGate(exponent=1 / 2 ** (k - j))(q[k], q[j])
    for j in range(n // 2):
        yield cirq.SWAP(q[j], q[n - 1 - j])


CIRCUITS = {"ghz": ghz, "random": random, "qft": qft}


def prepare(circuit, n, _device):
    qubits = cirq.LineQubit.range(n)
    sim = cirq.Simulator(dtype=np.complex128, seed=SEED)

    def build():
        return cirq.Circuit(CIRCUITS[circuit](qubits))

    built = build()

    def run():
        return sim.simulate(built, qubit_order=qubits)

    return build, run, len(list(built.all_operations()))
