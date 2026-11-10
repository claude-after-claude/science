"""Step 2 of NOTES, checked without thinking: for random odd x_1..x_k (nothing else assumed),
how often is  N - (N/x_1 + ... + N/x_k + 1)  divisible by 4?   The claim is: always when
4 | k, never otherwise - so (*) can hold in odd integers only when 4 | k."""
import random, math
rng = random.Random(1)
T = 20000
for k in range(2, 25):
    z = 0
    for _ in range(T):
        xs = [rng.randrange(1, 10**6) * 2 + 1 for _ in range(k)]
        N = math.prod(xs)
        z += (N - sum(N // x for x in xs) - 1) % 4 == 0
    assert z == (T if k % 4 == 0 else 0)
    print(f"k = {k:2d}:  divisible by 4 in {z:5d} of {T} trials")
