import numpy as np
from scipy.sparse import csr_matrix

from cipher.utils import binaryproduct, bit_flipping, gauss_jordan

class LDPC:
    def __init__(self, G, H):
        self.G = G
        self.H = H

    @classmethod
    def from_params(cls, n, d_v, d_c):
        H, G = make_ldpc(n, d_v, d_c)
        return cls(G.T, H)

    def encode(self, word):
        return (word @ self.G) % 2

    def decode(self, codeword):
        return bit_flipping(self.H, codeword)

    def get_message(self, decoded):
        return decoded[:self.G.shape[0]]

def parity_check_matrix(n_code, d_v, d_c):
    rng = np.random.mtrand._rand

    if d_v <= 1:
        raise ValueError("""d_v must be at least 2.""")

    if d_c <= d_v:
        raise ValueError("""d_c must be greater than d_v.""")

    if n_code % d_c:
        raise ValueError("""d_c must divide n for a regular LDPC matrix H.""")

    n_equations = (n_code * d_v) // d_c

    block = np.zeros((n_equations // d_v, n_code), dtype=int)
    H = np.empty((n_equations, n_code))
    block_size = n_equations // d_v


    for i in range(block_size):
        for j in range(i * d_c, (i+1) * d_c):
            block[i, j] = 1
    H[:block_size] = block

    for i in range(1, d_v):
        H[i * block_size: (i + 1) * block_size] = rng.permutation(block.T).T
    return H.astype(int)


def coding_matrix_systematic(H):
    n_equations, n_code = H.shape
    sparse = True

    P1 = np.identity(n_code, dtype=int)

    Hrowreduced = gauss_jordan(H)

    n_bits = n_code - sum([a.any() for a in Hrowreduced])

    while True:
        zeros = [i for i in range(min(n_equations, n_code)) if not Hrowreduced[i, i]]
        if len(zeros):
            indice_colonne_a = min(zeros)
        else:
            break

        ones = [j for j in range(indice_colonne_a + 1, n_code) if Hrowreduced[indice_colonne_a, j]]
        if len(ones):
            indice_colonne_b = min(ones)
        else:
            break

        aux = Hrowreduced[:, indice_colonne_a].copy()
        Hrowreduced[:, indice_colonne_a] = Hrowreduced[:, indice_colonne_b]
        Hrowreduced[:, indice_colonne_b] = aux

        aux = P1[:, indice_colonne_a].copy()
        P1[:, indice_colonne_a] = P1[:, indice_colonne_b]
        P1[:, indice_colonne_b] = aux

    P1 = P1.T
    identity = list(range(n_code))
    sigma = identity[n_code - n_bits:] + identity[:n_code - n_bits]

    P2 = np.zeros(shape=(n_code, n_code), dtype=int)
    P2[identity, sigma] = np.ones(n_code)

    if sparse:
        P1 = csr_matrix(P1)
        P2 = csr_matrix(P2)
        H = csr_matrix(H)

    P = binaryproduct(P2, P1)

    if sparse:
        P = csr_matrix(P)

    H_new = binaryproduct(H, np.transpose(P))

    G_systematic = np.zeros((n_bits, n_code), dtype=int)
    G_systematic[:, :n_bits] = np.identity(n_bits)
    G_systematic[:, n_bits:] = (Hrowreduced[:n_code - n_bits, n_code - n_bits:]).T

    return H_new, G_systematic.T


def make_ldpc(n_code, d_v, d_c):
    H = parity_check_matrix(n_code, d_v, d_c)
    return coding_matrix_systematic(H)