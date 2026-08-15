"""
Qulacs backend
"""

import numpy as np
from qulacs import QuantumCircuit, QuantumState
from qulacs.gate import U1, to_matrix_gate

FRAMEWORK = "qulacs"
SEED = 1234

# Qulacs rotations run the opposite way round; see the docstring.
ROT_SIGN = -1.0


def ghz(n):
    c = QuantumCircuit(n)
    c.add_H_gate(0)
    for q in range(n - 1):
        c.add_CNOT_gate(q, q + 1)
    return c


def random(n):
    # Square circuit: depth == width, the usual convention for random-circuit
    # benchmarking. Same seed, same draw order and same gate set in every
    # framework, so all of them build the identical circuit.
    angles = np.random.default_rng(SEED).uniform(0, 2 * np.pi, size=(n, n, 2))
    c = QuantumCircuit(n)
    for layer in range(n):
        for q in range(n):
            c.add_RX_gate(q, ROT_SIGN * angles[layer, q, 0])
            c.add_RZ_gate(q, ROT_SIGN * angles[layer, q, 1])
        for q in range(layer % 2, n - 1, 2):  # brickwork: alternate the pairing
            c.add_CZ_gate(q, q + 1)
    return c


def qft(n):
    c = QuantumCircuit(n)
    for j in range(n):
        c.add_H_gate(j)
        for k in range(j + 1, n):
            # U1(t) is diag(1, exp(i t)); with a control it becomes CP(t).
            gate = to_matrix_gate(U1(j, np.pi / 2 ** (k - j)))
            gate.add_control_qubit(k, 1)
            c.add_gate(gate)
    for j in range(n // 2):
        c.add_SWAP_gate(j, n - 1 - j)
    return c


CIRCUITS = {"ghz": ghz, "random": random, "qft": qft}


def prepare(circuit, n, _device):
    def build():
        return CIRCUITS[circuit](n)

    built = build()

    def run():
        # Allocation is inside the timed section to match Aer, which also
        # allocates its statevector inside run().
        state = QuantumState(n)
        built.update_quantum_state(state)
        return state

    def get_state(result):
        # Already little-endian, same as Qiskit - no reordering needed.
        return np.asarray(result.get_vector(), dtype=np.complex128)

    return build, run, built.get_gate_count(), get_state
