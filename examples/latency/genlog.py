"""genlog: a synthetic access log for latency.py, the same on every run.

usage: python3 genlog.py REQUESTS > LOG
Each line is a request: its time, method, path, status, latency in milliseconds (0.1 ms) and
response size in bytes. The endpoints get their shares of the requests, and each its own latency,
log-normal around its median (exp() of an Irwin-Hall sum of 12 uniform draws, a normal one), with
1 request in 100 ten times slower, its own response sizes and its own rate of errors (503s, which
are fast, and 504s, gateway timeouts logged with "-" for the latency). The draws come from a linear
congruential generator, so that the log is the same on every run.
"""
import math
import sys

# method, path, share of the requests, median latency (ms), its spread (sigma of its log), typical
# response size (bytes), errors per 10,000 requests
ENDPOINTS = [
    ("GET", "/api/users", 30, 12.0, 0.35, 2400, 5),
    ("GET", "/api/orders", 20, 28.0, 0.45, 9800, 12),
    ("POST", "/api/orders", 6, 65.0, 0.40, 600, 30),
    ("GET", "/static/app.js", 24, 1.8, 0.25, 182000, 1),
    ("GET", "/api/search", 12, 85.0, 0.65, 15500, 40),
    ("POST", "/api/login", 5, 140.0, 0.30, 350, 8),
    ("GET", "/healthz", 3, 0.6, 0.20, 2, 0),
]
TOTAL_SHARE = 100

seed = 20261013


def uniform() -> float:
    # a float in [0, 1): a 31-bit linear congruential generator (glibc's constants), whose products
    # stay in 64 bits, as Pystachy's ints do
    global seed
    seed = (seed * 1103515245 + 12345) % 2147483648
    return seed / 2147483648.0


def normal() -> float:
    # about normal: the sum of 12 uniform draws, less 6 (mean 0, variance 1)
    total = 0.0
    for _ in range(12):
        total += uniform()
    return total - 6.0


def timestamp(ms: int) -> str:
    # 2026-10-13T08:00:00.000 plus ms milliseconds, within the day
    s, milli = divmod(ms, 1000)
    m, sec = divmod(s, 60)
    h, minute = divmod(m, 60)
    return f"2026-10-13T{8 + h:02d}:{minute:02d}:{sec:02d}.{milli:03d}"


def request(clock: int) -> str:
    # one log line, at clock milliseconds past 08:00
    pick = uniform() * TOTAL_SHARE
    k = 0
    while pick >= ENDPOINTS[k][2] and k < len(ENDPOINTS) - 1:
        pick -= ENDPOINTS[k][2]
        k += 1
    method, path, _, median_ms, sigma, size, errors = ENDPOINTS[k]
    ms = median_ms * math.exp(sigma * normal())
    if uniform() < 0.01:
        ms *= 10.0
    status = 200
    body = int(size * (0.5 + uniform()))
    latency = f"{ms:.1f}"
    if uniform() * 10000 < errors:
        if uniform() < 0.5:
            status, body, latency = 503, 120, f"{0.3 + uniform():.1f}"
        else:
            status, body, latency = 504, 0, "-"
    elif method == "POST" and uniform() < 0.02:
        status = 400
    return f"{timestamp(clock)} {method} {path} {status} {latency} {body}"


def lines(n: int) -> list[str]:
    # the first n lines of the log
    out: list[str] = []
    clock = 0
    for _ in range(n):
        clock += int(uniform() * 12.0)
        out.append(request(clock))
    return out


def main() -> None:
    n = int(sys.argv[1])
    clock = 0
    for _ in range(n):
        clock += int(uniform() * 12.0)
        print(request(clock))


if __name__ == "__main__":
    main()
