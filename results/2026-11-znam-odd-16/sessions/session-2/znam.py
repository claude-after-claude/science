#!/usr/bin/env python3
"""
Znam's problem by exhaustive search (see ../linden/znam for the statement).

    python3 znam.py K              search length K from scratch, print everything (fine for K <= 7)
    python3 znam.py K --resume     same search, but checkpointed in progress-K.log next to this file;
                                   safe to kill and restart, picks up where it stopped (meant for K = 8)
    python3 znam.py K --status     how far a checkpointed search has got

"Improper" solutions: x_1 < ... < x_K with every x_i dividing (product of the others) + 1.
That is the same as   1/x_1 + ... + 1/x_K + 1/(x_1...x_K) = 1.
Znam's problem proper also demands x_i != (product of the others) + 1.

Search state: P = product of the terms chosen so far, N/P = what is left of 1.
(Terms are pairwise coprime, so N/P is automatically in lowest terms.)

With two terms y < z left to choose:   (N y - P)(N z - P) = P^2 + N,
so one factorisation of P^2 + N settles it.  Factoring is done by piping to coreutils `factor`.

Shortcut used when N is large compared with P (no factoring needed):
    S = y + z  must be  = -1/P (mod N),  y z = (1 + P S)/N,  and  S^2 - 4 y z  must be a square.
S is squeezed between 2P/N and a bound coming from y > (previous term), so if that window holds
few multiples of N we just try them all.
"""
import sys, os, subprocess, json, time
from math import gcd, isqrt

HERE = os.path.dirname(os.path.abspath(__file__))
S_LIMIT = 2000      # use the shortcut when at most this many candidates for S
CHUNK = 4000        # x-values per checkpointed unit of work

def factor_many(ns):
    if not ns: return []
    out = subprocess.run(['factor'], input='\n'.join(map(str, ns)), capture_output=True, text=True, check=True).stdout
    res = []
    for line in out.strip().split('\n'):
        d = {}
        for p in line.split(':')[1].split():
            p = int(p); d[p] = d.get(p, 0) + 1
        res.append(d)
    return res

def divisors(fd):
    ds = [1]
    for p, e in fd.items():
        ds = [d * p**i for d in ds for i in range(e + 1)]
    return ds

def two_by_factoring(P, N, lo, fd):
    n = P * P + N
    sols = []
    for d in divisors(fd):
        e = n // d
        if d >= e or (d + P) % N: continue
        y, z = (d + P) // N, (e + P) // N
        if y > lo: sols.append((y, z))
    return sols

def s_window(P, N, lo):
    """Candidates for S = y + z: (first, last, step); empty if first > last."""
    ymin = max(lo + 1, P // N + 1)
    smax = ymin + (P * ymin + 1) // (N * ymin - P)
    smin = 2 * P // N + 1
    r = (-pow(P, -1, N)) % N if N > 1 else 0
    first = smin + ((r - smin) % N)
    return first, smax, N

def two_by_window(P, N, lo, win):
    first, smax, step = win
    sols = []
    for S in range(first, smax + 1, step):
        D = S * S - 4 * ((1 + P * S) // N)
        if D <= 0: continue
        s = isqrt(D)
        if s * s == D and (S - s) % 2 == 0:
            y, z = (S - s) // 2, (S + s) // 2
            if y > lo: sols.append((y, z))
    return sols

def last_three(prefix, P, N, a, b, use_window=True):
    """All completions prefix + [x, y, z] with a <= x < b.  Returns (sols, n_factored, n_windowed)."""
    tofactor, sols, nw = [], [], 0
    for x in range(a, b):
        if gcd(x, P) != 1: continue
        N2 = N * x - P
        if N2 <= 0: continue
        P2 = P * x
        if use_window:
            win = s_window(P2, N2, x)
            if (win[1] - win[0]) // win[2] < S_LIMIT:
                nw += 1
                for y, z in two_by_window(P2, N2, x, win): sols.append(prefix + [x, y, z])
                continue
        tofactor.append((x, P2, N2))
    for (x, P2, N2), fd in zip(tofactor, factor_many([P2 * P2 + N2 for _, P2, N2 in tofactor])):
        for y, z in two_by_factoring(P2, N2, x, fd): sols.append(prefix + [x, y, z])
    return sols, len(tofactor), nw

def x_range(prefix, P, N, m):
    lo = prefix[-1] if prefix else 1
    return max(lo + 1, P // N + 1), (m * P + 1) // N + 1

def prefixes(prefix, P, N, m, out):
    """All prefixes that leave exactly three terms to choose."""
    if m == 3:
        out.append((prefix, P, N)); return
    a, b = x_range(prefix, P, N, m)
    for x in range(a, b):
        if gcd(x, P) != 1: continue
        N2 = N * x - P
        if N2 > 0: prefixes(prefix + [x], P * x, N2, m - 1, out)

def check(s):
    prod = 1
    for x in s: prod *= x
    return all(a < b for a, b in zip(s, s[1:])) and all((prod // x + 1) % x == 0 for x in s)

def proper(s):
    prod = 1
    for x in s: prod *= x
    return all(prod // x + 1 != x for x in s)

def tasks_for(K):
    pres = []
    prefixes([], 1, 1, K, pres)
    sized = sorted(pres, key=lambda t: x_range(t[0], t[1], t[2], 3)[1] - x_range(t[0], t[1], t[2], 3)[0])
    tasks = []
    for pre, P, N in sized:
        a, b = x_range(pre, P, N, 3)
        for s in range(a, b, CHUNK):
            tasks.append((pre, P, N, s, min(b, s + CHUNK)))
    return tasks

def tid(t):
    return ','.join(map(str, t[0])) + f':{t[3]}-{t[4]}'

def read_log(K):
    done, sols = {}, []
    path = os.path.join(HERE, f'progress-{K}.log')
    if os.path.exists(path):
        for line in open(path):
            try: rec = json.loads(line)
            except ValueError: continue          # a torn last line from a kill; that chunk just gets redone
            done[rec['id']] = rec
            sols.extend(rec['sols'])
    return path, done, sols

def report(K, sols):
    sols = sorted(set(map(tuple, sols)))
    assert all(check(s) for s in sols)
    pr = [s for s in sols if proper(s)]
    print(f"K={K}: {len(sols)} improper solutions, of which {len(pr)} proper (Znam)")
    return sols

if __name__ == '__main__':
    K = int(sys.argv[1]); mode = sys.argv[2] if len(sys.argv) > 2 else ''
    if K < 3: sys.exit("K >= 3 please")
    tasks = tasks_for(K)
    if mode == '':
        sols = []
        for pre, P, N, a, b in tasks: sols += last_three(pre, P, N, a, b)[0]
        for s in report(K, sols): print(('  ' if proper(s) else '* ') + ' '.join(map(str, s)))
    else:
        path, done, sols = read_log(K)
        total = sum(t[4] - t[3] for t in tasks)
        got = sum(t[4] - t[3] for t in tasks if tid(t) in done)
        print(f"{len(done)}/{len(tasks)} chunks done, {100*got/total:.2f}% of the x-range; "
              f"{sum(r['secs'] for r in done.values())/3600:.2f} cpu-hours logged")
        if mode == '--resume':
            with open(path, 'a') as f:
                t0 = time.time()
                for t in tasks:
                    if tid(t) in done: continue
                    t1 = time.time()
                    s, nf, nw = last_three(*t)
                    rec = {'id': tid(t), 'factored': nf, 'windowed': nw, 'secs': round(time.time() - t1, 2), 'sols': s}
                    f.write(json.dumps(rec) + '\n'); f.flush()
                    done[rec['id']] = rec; sols += s; got += t[4] - t[3]
                    if time.time() - t0 > 60:
                        t0 = time.time()
                        print(f"  {100*got/total:.2f}%  {len(set(map(tuple, sols)))} solutions so far", flush=True)
            print("search complete.")
        sols = report(K, sols)
        if len(done) < len(tasks): print("(search not finished: these counts are lower bounds)")
        with open(os.path.join(HERE, f'solutions-{K}{"" if len(done) == len(tasks) else "-partial"}.txt'), 'w') as f:
            for s in sols: f.write(('  ' if proper(s) else '* ') + ' '.join(map(str, s)) + '\n')
