import numpy as np

from random import randint
from struct import pack, unpack

from cipher.code import LDPC
from cipher.utils import bytes_to_codeword, codeword_to_bytes, dump, gauss_jordan, load


class Crypter:
    def __init__(self, code, S, P, errors=10):
        self.S = S
        self.P = P
        self.errors = errors
        self.code = code
        self.k, self.n = code.G.shape
        self.public_key = self.S @ self.code.G @ self.P % 2

    @classmethod 
    def from_code(cls, code: LDPC):
        P = np.eye(code.G.shape[1], dtype=int) 
        np.random.shuffle(P) 
        return cls(code, Crypter.generate_nonsingular_matrix(code.G.shape[0]), P)

    def encrypt(self, pt):
        pt_word = bytes_to_codeword(pt, self.code.G.shape[0])
        z = np.array([1] * self.errors + [0] * (self.n - self.errors), dtype=int)
        np.random.shuffle(z)
        return codeword_to_bytes(((pt_word @ self.public_key % 2) + z) % 2)

    def decrypt(self, ct):
        ct_word = bytes_to_codeword(ct, self.code.G.shape[1])
        A, P_inv = gauss_jordan(self.P, True)
        c = np.array(ct_word @ P_inv % 2, dtype=int)
        m = self.code.get_message(self.code.decode(c))
        S_inv = gauss_jordan(self.S, True)[1]
        return codeword_to_bytes(m @ S_inv % 2)

    @staticmethod
    def generate_nonsingular_matrix(k):
        while True:
            S = np.random.randint(0, 2, (k, k))
            A = np.array(gauss_jordan(S), dtype=int)
            if (A == np.eye(k, dtype=int)).all():
                return S

    def dump_private(self):
        matrixes = [self.S, self.P, self.code.G, self.code.H]
        return b''.join((pack('<H', len(x)) + x) for x in map(dump, matrixes))

    def dump_public(self):
        pub_dump = dump(self.public_key)
        return pack('<H', len(pub_dump)) + pub_dump

    @classmethod
    def load_private(cls, data):
        matrixes = []
        while data:
            size = unpack('<H', data[:2])[0]
            dump, data = data[2:size+2], data[size+2:]
            matrixes.append(load(dump))
        S, P, G, H = matrixes
        return cls(LDPC(G, H), S, P)