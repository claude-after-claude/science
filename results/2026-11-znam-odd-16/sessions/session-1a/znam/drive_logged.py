"""drive.py, unchanged, with one thing added: every integer >= psi_12 that the search treats
as prime on the strength of the Miller-Rabin test is appended to bigprimes.k{k}.<pid>.
(Sorted and merged, that list is what ../primality certifies.)

    BMAX=30000000 CHUNK=100000 python3 drive_logged.py 8 2
    sort -un bigprimes.k8.* > bigprimes.k8 && rm bigprimes.k8.*

The search asks "is this prime?" in two places: drive.leaf (the cofactor left by the sieve)
and znam.factor (the pieces rho splits off).  Both go through the wrapper below.
"""
import os, sys
import znam, drive

PSI12 = 318665857834031151167461
_plain = znam.is_prime
_log = None
def is_prime(n):
    global _log
    ok = _plain(n)
    if ok and n >= PSI12:
        if _log is None or _log[0] != os.getpid():       # one file per worker process
            _log = (os.getpid(), open(f"bigprimes.k{sys.argv[1]}.{os.getpid()}", "a", buffering=1))
        _log[1].write(f"{n}\n")
    return ok

znam.is_prime = is_prime      # znam.factor looks the name up when called
drive.is_prime = is_prime     # drive.leaf likewise

if __name__ == "__main__":
    drive.main()
