"""
Amazon Braket local simulator backend
"""

import numpy as np
from braket.circuits import Circuit
from braket.devices import LocalSimulator

FRAMEWORK = "braket"
SEED = 1234


def ghz(n):
    c = Circuit().h(0)
    for q in range(n - 1):
        c.cnot(q, q + 1)
    return c


def random(n):
    # Square circuit: depth == width, the usual convention for random-circuit
    # benchmarking. Same seed, same draw order and same gate set in every
    # framework, so all of them build the identical circuit.
    angles = np.random.default_rng(SEED).uniform(0, 2 * np.pi, size=(n, n, 2))
    c = Circuit()
    for layer in range(n):
        for q in range(n):
            c.rx(q, angles[layer, q, 0])
            c.rz(q, angles[layer, q, 1])
        for q in range(layer % 2, n - 1, 2):  # brickwork: alternate the pairing
            c.cz(q, q + 1)
    return c


def qft(n):
    c = Circuit()
    for j in range(n):
        c.h(j)
        for k in range(j + 1, n):
            # cphaseshift(control, target, angle) is diag(1,1,1,exp(i*angle)).
            c.cphaseshift(k, j, np.pi / 2 ** (k - j))
    for j in range(n // 2):
        c.swap(j, n - 1 - j)
    return c


CIRCUITS = {"ghz": ghz, "random": random, "qft": qft}


def prepare(circuit, n, _device):
    sim = LocalSimulator("braket_sv")

    def build():
        c = CIRCUITS[circuit](n)
        c.state_vector()
        return c

    built = build()

    def run():
        return sim.run(built, shots=0).result()

    return build, run, len(built.instructions)
