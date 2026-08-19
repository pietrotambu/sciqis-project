"""
PennyLane Lightning backend
"""

import numpy as np
import pennylane as qml
from pennylane.tape import QuantumScript

FRAMEWORK = "pennylane"
SEED = 1234

_DEVICE_NAMES = {"cpu": "lightning.qubit", "gpu": "lightning.gpu"}


def ghz(n):
    ops = [qml.Hadamard(0)]
    ops += [qml.CNOT([q, q + 1]) for q in range(n - 1)]
    return ops


def random(n):
    # Square circuit: depth == width
    # benchmarking. Same seed, same draw order and same gate set in every
    # framework, so all of them build the identical circuit.
    angles = np.random.default_rng(SEED).uniform(0, 2 * np.pi, size=(n, n, 2))
    ops = []
    for layer in range(n):
        for q in range(n):
            ops.append(qml.RX(angles[layer, q, 0], q))
            ops.append(qml.RZ(angles[layer, q, 1], q))
        for q in range(layer % 2, n - 1, 2):
            ops.append(qml.CZ([q, q + 1]))
    return ops


def qft(n):
    ops = []
    for j in range(n):
        ops.append(qml.Hadamard(j))
        for k in range(j + 1, n):
            ops.append(qml.ControlledPhaseShift(np.pi / 2 ** (k - j), [k, j]))
    for j in range(n // 2):
        ops.append(qml.SWAP([j, n - 1 - j]))
    return ops


CIRCUITS = {"ghz": ghz, "random": random, "qft": qft}


def prepare(circuit, n, device):
    dev = qml.device(_DEVICE_NAMES[device], wires=n, c_dtype=np.complex128)

    def build():
        return QuantumScript(CIRCUITS[circuit](n), [qml.state()])

    tape = build()

    def run():
        return dev.execute(tape)

    return build, run, len(tape.operations)
