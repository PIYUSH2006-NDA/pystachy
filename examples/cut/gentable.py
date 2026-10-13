"""gentable: a synthetic tab-separated table for cut.py, the same on every run.

usage: python3 gentable.py N > TABLE
Each of the N lines is a row of 8 fields: an id, a timestamp, a user, a service, an operation, a
status code, a duration in ms and a short message of a few words. One line in 50 is a comment
without tabs, which cut prints as it is (or drops with -s).
"""
import sys

USERS = ["ana", "bo", "chen", "dara", "eli", "fay", "gus", "hana", "ivo", "jun", "kai", "lea"]
SERVICES = ["auth", "billing", "search", "upload", "gateway", "queue", "cache", "db"]
OPERATIONS = ["login", "logout", "charge", "refund", "query", "put", "get", "sync", "render"]
WORDS = ["ok", "slow", "retry", "cold", "start", "cache", "miss", "hit", "timeout", "user", "quota",
         "exceeded", "token", "expired", "done", "partial", "write", "read", "lock", "wait"]

seed = 20261013


def rand(n: int) -> int:
    # an int in [0, n): a 31-bit linear congruential generator (glibc's constants), whose products
    # stay in 64 bits, as Pystachy's ints do
    global seed
    seed = (seed * 1103515245 + 12345) % 2147483648
    return (seed >> 8) % n


def row(i: int) -> str:
    if rand(50) == 0:
        return f"# checkpoint {i}"
    message = " ".join([WORDS[rand(len(WORDS))] for _ in range(1 + rand(5))])
    status = [200, 200, 200, 201, 204, 301, 404, 500, 503][rand(9)]
    fields = [str(i), str(1760000000 + i * 3), USERS[rand(len(USERS))], SERVICES[rand(len(SERVICES))],
              OPERATIONS[rand(len(OPERATIONS))], str(status), str(rand(5000)), message]
    return "\t".join(fields)


def main() -> None:
    n = int(sys.argv[1])
    for i in range(n):
        print(row(i))


if __name__ == "__main__":
    main()
