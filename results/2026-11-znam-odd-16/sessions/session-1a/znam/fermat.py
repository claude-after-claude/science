"""Find all (y,z), y<=z, with r*y*z - P*(y+z) = 1 and d = y*r-P >= dmin.

sigma = y+z lies in one residue class mod r, and y,z are integers iff
    Delta(sigma) = sigma^2 - 4(P sigma + 1)/r   is a perfect square.
Along the progression sigma_j = s + j r, Delta is a quadratic in j.  Squares are sieved with
big-int bitmasks: for each small modulus q, the q-periodic pattern of "Delta is a square mod q"
is replicated by one multiplication and ANDed in.  For long ranges, a wheel on the first few
moduli splits j into residue classes so only ~W*density bit-vectors of length K/W are touched."""
from math import isqrt

SIZES = [1 << i for i in range(6, 21)]
CH = SIZES[-1]
MODS = [64, 9, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97]
QR = {}
REP = {}     # (q, size) -> repunit of period q covering `size` bits
for q in MODS:
    sq = {(v * v) % q for v in range(q)}
    QR[q] = [v in sq for v in range(q)]
    for sz in SIZES:
        REP[q, sz] = ((1 << (q * (sz // q + 1))) - 1) // ((1 << q) - 1)
# wheels: (number of leading moduli used, W)
WHEELS = [(0, 1), (2, 576), (3, 2880), (4, 20160), (5, 221760), (6, 2882880)]
REPW = {}
for m, W in WHEELS:
    for q in MODS[:m]:
        REPW[q, W] = ((1 << W) - 1) // ((1 << q) - 1)

_pat = {}
_base = {}
ODDP = set(MODS[2:])
FULL = {q: (1 << q) - 1 for q in MODS}
INV2A = {q: [0] + [pow(2 * a, -1, q) for a in range(1, q)] for q in MODS[2:]}
def pattern(q, a, b, c):
    """q-bit mask: bit j set iff a j^2 + b j + c is a square mod q"""
    if a and q in ODDP:
        # complete the square: a (j+h)^2 + c', pattern is a rotation of the (a, 0, c') pattern
        h = b * INV2A[q][a] % q
        cp = (c - a * h * h) % q
        key = (q, a, cp)
        base = _base.get(key)
        if base is None:
            t = QR[q]; base = 0
            for j in range(q):
                if t[(a * j * j + cp) % q]: base |= 1 << j
            _base[key] = base
        if h: return ((base >> h) | (base << (q - h))) & FULL[q]
        return base
    key = (q, a, b, c)
    p = _pat.get(key)
    if p is None:
        if len(_pat) > 500_000: _pat.clear()
        t = QR[q]; p = 0
        for j in range(q):
            if t[(a * j * j + b * j + c) % q]: p |= 1 << j
        _pat[key] = p
    return p

def _squares_direct(A, B, C, n, mods, out, scale, off):
    """indices j in [0,n) with A j^2 + B j + C a perfect square; appends off + scale*j"""
    i0 = 0
    while i0 < n:
        m = min(CH, n - i0)
        Bs = 2 * A * i0 + B
        Cs = (A * i0 + B) * i0 + C
        if m <= 24:
            for j in range(m):
                D = (A * j + Bs) * j + Cs
                if D >= 0:
                    w = isqrt(D)
                    if w * w == D: out.append((off + scale * (i0 + j), w))
        else:
            for sz in SIZES:
                if sz >= m: break
            mask = (1 << m) - 1
            for q in mods:
                mask &= pattern(q, A % q, Bs % q, Cs % q) * REP[q, sz]
                if not mask: break
            while mask:
                low = mask & -mask
                j = low.bit_length() - 1
                mask ^= low
                D = (A * j + Bs) * j + Cs
                if D >= 0:
                    w = isqrt(D)
                    if w * w == D: out.append((off + scale * (i0 + j), w))
        i0 += m

def squares(A, B, C, K, wheel=None):
    """all (j, w) with 0 <= j < K and A j^2 + B j + C = w^2"""
    out = []
    if wheel is None:
        wheel = 0 if K < 60_000 else 1 if K < 20_000_000 else 2 if K < 60_000_000 else 3 if K < 3_000_000_000 else 4
    m, W = WHEELS[wheel]
    if m == 0:
        _squares_direct(A, B, C, K, MODS, out, 1, 0)
        return out
    allowed = (1 << W) - 1
    for q in MODS[:m]:
        allowed &= pattern(q, A % q, B % q, C % q) * REPW[q, W]
    rest = MODS[m:]
    AW = A * W; A2 = AW * W
    while allowed:
        low = allowed & -allowed
        rho = low.bit_length() - 1
        allowed ^= low
        if rho >= K: break
        n = (K - rho + W - 1) // W
        _squares_direct(A2, (2 * A * rho + B) * W, (A * rho + B) * rho + C, n, rest, out, W, rho)
    return out

def scan(P, r, N, dmin, wheel=None):
    sig0 = (-pow(P, -1, r)) % r if r > 1 else 0
    s_lo = (2 * (P + isqrt(N))) // r
    s_hi = (dmin + N // dmin + 2 * P) // r + 1
    s_s = s_lo + ((sig0 - s_lo) % r)
    if s_s > s_hi: return []
    K = (s_hi - s_s) // r + 1
    A = r * r
    B = 2 * s_s * r - 4 * P
    C = s_s * s_s - 4 * ((P * s_s + 1) // r)
    res = []
    for j, w in squares(A, B, C, K, wheel):
        s = s_s + j * r
        res.append(((s - w) // 2, (s + w) // 2))
    return res
