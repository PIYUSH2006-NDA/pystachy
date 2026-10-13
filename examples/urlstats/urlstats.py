"""urlstats: what the requests of a web server's access log asked for, with urllib.parse.

usage: python3 urlstats.py [--top N] [--canon] [--time] LOG

It reads the request target of each line of a Common or Combined Log Format log ("GET
/search?q=caf%C3%A9 HTTP/1.1"), splits it with urlsplit(), decodes its path with unquote() and its
query with parse_qsl(), and reports the most requested paths, each query parameter with the number
of requests that give it, its distinct values and the most common ones, the values whose escapes
were no UTF-8, and the most requested canonical URLs: the path's segments decoded and quoted again
and the query's pairs sorted and encoded with urlencode(), so that "/caf%c3%a9?b=2&a=1" and
"/caf%C3%A9?a=1&b=2" are one URL, as a cache would key them. --canon prints the canonical URL of each request instead, and --time
writes how long the reading and the report took to stderr.
"""
import sys
import time
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit


class Stats:
    """What the requests of a log asked for."""

    def __init__(self) -> None:
        self.requests = 0
        self.skipped = 0  # lines without a request line
        self.paths: dict[str, int] = {}
        self.canonical: dict[str, int] = {}
        self.params: dict[str, int] = {}  # requests that give a parameter
        self.values: dict[str, dict[str, int]] = {}  # by parameter, its values' counts
        self.undecodable = 0  # values whose escapes are no UTF-8


def request_target(line: str) -> str:
    # the target of a log line's request line ("GET /path?query HTTP/1.1"), or "" if it has none
    i = line.find('"')
    j = line.find('"', i + 1)
    if i < 0 or j < 0:
        return ""
    words = line[i + 1 : j].split(" ")
    return words[1] if len(words) == 3 else ""


def canonical(path: str, pairs: list[tuple[str, str]]) -> str:
    # the path (as the request gives it), each of its segments decoded and quoted again, so that an
    # escaped "/" stays one, and the query's pairs sorted and encoded again (%20 for a space)
    path = "/".join([quote(unquote(segment), safe="") for segment in path.split("/")])
    query = urlencode(sorted(pairs), quote_via=quote)
    return path + "?" + query if query else path


def add(stats: Stats, target: str) -> str:
    # counts the request for target, and returns its canonical URL
    parts = urlsplit(target)
    path = unquote(parts.path)
    pairs = parse_qsl(parts.query, keep_blank_values=True)
    stats.requests += 1
    stats.paths[path] = stats.paths.get(path, 0) + 1
    seen: set[str] = set()
    for name, value in pairs:
        if name not in seen:
            seen.add(name)
            stats.params[name] = stats.params.get(name, 0) + 1
        counts = stats.values.setdefault(name, {})
        counts[value] = counts.get(value, 0) + 1
        if "�" in value:
            stats.undecodable += 1
    url = canonical(parts.path, pairs)
    stats.canonical[url] = stats.canonical.get(url, 0) + 1
    return url


def count_of(item: tuple[str, int]) -> tuple[int, str]:
    # the order of a report: the most frequent first, then by name
    return (-item[1], item[0])


def top(counts: dict[str, int], n: int) -> list[tuple[str, int]]:
    return sorted(counts.items(), key=count_of)[:n]


def report(stats: Stats, n: int) -> list[str]:
    out = [f"{stats.requests} requests ({stats.skipped} lines without one); {len(stats.paths)} distinct paths, "
           f"{len(stats.canonical)} distinct canonical URLs"]
    out.append("most requested paths:")
    for path, count in top(stats.paths, n):
        out.append(f"  {count:8} {path}")
    out.append("query parameters: requests that give them, distinct values, the most common values:")
    for name, count in top(stats.params, len(stats.params)):
        values = stats.values[name]
        common = ", ".join([f"{v!r} ({c})" for v, c in top(values, 3)])
        out.append(f"  {name:10} {count:8} {len(values):6}  {common}")
    out.append(f"values whose escapes are no UTF-8 (decoded with U+FFFD): {stats.undecodable}")
    out.append("most requested canonical URLs:")
    for url, count in top(stats.canonical, n):
        out.append(f"  {count:8} {url}")
    return out


def main() -> None:
    args = sys.argv[1:]
    n = 10
    canon = False
    timing = False
    while len(args) > 1:
        if args[0] == "--top":
            n = int(args[1])
            args = args[2:]
        elif args[0] == "--canon":
            canon = True
            args = args[1:]
        elif args[0] == "--time":
            timing = True
            args = args[1:]
        else:
            break
    if len(args) != 1:
        print("usage: urlstats.py [--top N] [--canon] [--time] LOG", file=sys.stderr)
        sys.exit(2)
    stats = Stats()
    t0 = time.perf_counter()
    with open(args[0]) as f:
        for line in f:
            target = request_target(line)
            if not target:
                stats.skipped += 1
                continue
            url = add(stats, target)
            if canon:
                print(url)
    t1 = time.perf_counter()
    if not canon:
        for row in report(stats, n):
            print(row)
    if timing:
        print(f"read {t1 - t0:.3f} s, report {time.perf_counter() - t1:.3f} s", file=sys.stderr)


if __name__ == "__main__":
    main()
