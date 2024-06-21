import numpy as np
import zlib
from random import choice
from struct import pack, unpack

def int_to_bytes(x) -> bytes:
    return x.to_bytes((x.bit_length() + 7) // 8, 'big')
    
def bytes_to_int(xbytes) -> int:
    return int.from_bytes(xbytes, 'big')

def bytes_to_codeword(x, size):
    data = list(map(int, bin(bytes_to_int(x))[2:]))
    return np.array([0]*(size-len(data)) + data)

def codeword_to_bytes(x):
    return int_to_bytes(int(''.join(map(str, x)), 2))

def dump(M):
    size = pack('<2H', *M.shape)
    return size + zlib.compress(int_to_bytes(int(''.join(map(str, [1] + list(M.flatten()))), 2)))

def load(data):
    size = unpack('<2H', data[:4])
    return np.array(list(map(int, bin(bytes_to_int(zlib.decompress(data[4:])))[3:]))).reshape(size)


def binaryproduct(X, Y):
    A = X.dot(Y)
    try:
        A = A.toarray()
    except AttributeError:
        pass
    return A % 2


def gauss_jordan(X, change=0):
    A = np.copy(X)
    m, n = A.shape

    if change:
        P = np.identity(m).astype(int)

    pivot_old = -1
    for j in range(n):
        filtre_down = A[pivot_old+1:m, j]
        pivot = np.argmax(filtre_down)+pivot_old+1

        if A[pivot, j]:
            pivot_old += 1
            if pivot_old != pivot:
                aux = np.copy(A[pivot, :])
                A[pivot, :] = A[pivot_old, :]
                A[pivot_old, :] = aux
                if change:
                    aux = np.copy(P[pivot, :])
                    P[pivot, :] = P[pivot_old, :]
                    P[pivot_old, :] = aux

            for i in range(m):
                if i != pivot_old and A[i, j]:
                    if change:
                        P[i, :] = abs(P[i, :]-P[pivot_old, :])
                    A[i, :] = abs(A[i, :]-A[pivot_old, :])

        if pivot_old == m-1:
            break

    return (A, P) if change else A

def bit_flipping(H, c, maxiter=200):
    n, k = H.shape
    
    Cn = {i : set() for i in range(n)} # check nodes
    Vn = {i : set() for i in range(k)} # variable nodes
    
    for i in range(n):
        for j in range(k):
            if H[i][j] == 1:
                Cn[i].add(j)
                Vn[j].add(i)
                
    def fix_errors(c, iteration):
        En = np.zeros(k, dtype=int)
        Sn = np.zeros(n, dtype=int)
        
        if iteration == 0:
            return
        
        for node, relations in Cn.items():
            Sn[node] = sum(c[list(relations)]) % 2
        
        for node, check in enumerate(Sn):
            if check == 1:
                for relation in Cn[node]:
                    En[relation] += 1
                    
        if sum(En) == 0:
            return
        
        m = 0
        max_indexes = []
        for i, elem in enumerate(En):
            if elem == m and m > 0:
                max_indexes.append(i)
            elif elem > m:
                max_indexes = []
                m = elem
                max_indexes.append(i)
            
        flip = choice(max_indexes)
        c[flip] = 1 if c[flip] == 0 else 0
        
        fix_errors(c, iteration-1)
    
    fix_errors(c, maxiter)
    
    return c
