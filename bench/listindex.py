# Checked list[int] subscripts in a range loop. The JIT cannot inline pys_list_get from
# the runtime, while listfast emits the non-negative, in-bounds read in the program.
# Optional: ./pystachy run bench/listindex.py 100000 --time (100M reads; process CPU time).
import sys
import time


def total(xs: list[int]) -> int:
    out = 0
    for i in range(len(xs)):
        out += xs[i]
    return out


xs = list(range(1000))
rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
start = time.process_time()
out = 0
for _ in range(rounds):
    out += total(xs)
print(out)
if "--time" in sys.argv:
    print(time.process_time() - start)
