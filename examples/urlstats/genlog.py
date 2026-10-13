"""genlog: a synthetic web server access log for urlstats.py, the same on every run.

usage: python3 genlog.py LINES > LOG
Each line is a Combined Log Format line of a request to a shop: the front page, searches (q, page
and sort), products (with ref and utm_* tracking), categories (filter, given twice, and page), an
API, a login page with a next URL, and static files. Search terms mix ASCII and other scripts,
characters that must be escaped and terms clients send as they are. Clients encode them as they
do: with quote_plus() or quote(), upper or lower case hex digits, the parameters in any order, and
a few in Latin-1 (whose escapes are no UTF-8) or with a broken escape. The choices come from a
linear congruential generator, so the log is the same on every run, under CPython and compiled.
"""
import sys
from urllib.parse import quote, quote_plus

TERMS = ["shoes", "red dress", "caf\xe9", "cr\xe8me br\xfbl\xe9e", "na\xefve", "Stra\xdfe", "東京",
         "ラーメン", "Москва", "gift \U0001f381", "C++ book",
         "100% cotton", "rock & roll", "what?", "a+b", "t-shirt", "jeans", "lamp", "desk", "bike", "tent",
         "coffee", "tea", "socks", "hat"]
SORTS = ["price_asc", "price_desc", "newest", "rating"]
COLORS = ["red", "blue", "black", "white", "green"]
SIZES = ["S", "M", "L", "XL"]
CATEGORIES = ["women", "men", "kids", "home", "sport", "caf\xe9-bar"]
SOURCES = ["newsletter", "google", "facebook", "partner"]
AGENTS = ["Mozilla/5.0 (X11; Linux x86_64)", "Mozilla/5.0 (Macintosh)", "curl/8.5.0", "Googlebot/2.1"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

seed = 20261013


def rand(n: int) -> int:
    # an int in [0, n): a 31-bit linear congruential generator (glibc's constants), whose products
    # stay in 64 bits, as Pystachy's ints do
    global seed
    seed = (seed * 1103515245 + 12345) % 2147483648
    return (seed >> 8) % n


def lower_hex(s: str) -> str:
    # s with the hex digits of its escapes in lower case, as some clients write them
    parts = s.split("%")
    return parts[0] + "".join(["%" + p[:2].lower() + p[2:] for p in parts[1:]])


def encode(term: str) -> str:
    # term as a client puts it in a query: mostly quote_plus(), else quote() (%20 for a space), in
    # lower case hex digits, in Latin-1 (where it can), or as it is (a space as '+')
    k = rand(100)
    if k < 70:
        return quote_plus(term)
    if k < 85:
        return quote(term, safe="")
    if k < 93:
        return lower_hex(quote_plus(term))
    if k < 97:
        return quote_plus(term, encoding="latin-1", errors="replace")
    return term.replace(" ", "+").replace("&", "%26")


def query(pairs: list[str]) -> str:
    # the pairs in the order the client puts them: as given, or the first one last
    if len(pairs) > 1 and rand(4) == 0:
        pairs = pairs[1:] + pairs[:1]
    return "&".join(pairs)


def target() -> str:
    # a request's target: its path and query
    k = rand(100)
    if k < 8:
        return "/"
    if k < 40:
        pairs = ["q=" + encode(TERMS[rand(len(TERMS))])]
        if rand(3) == 0:
            pairs.append("page=%d" % (2 + rand(5)))
        if rand(4) == 0:
            pairs.append("sort=" + SORTS[rand(len(SORTS))])
        if rand(50) == 0:
            pairs.append("ref=%zz")
        return "/search?" + query(pairs)
    if k < 62:
        path = "/product/%d" % (1 + rand(2000))
        if rand(3) == 0:
            return path
        pairs = ["ref=" + ("home" if rand(2) else "search")]
        if rand(2) == 0:
            pairs.append("utm_source=" + SOURCES[rand(len(SOURCES))])
            pairs.append("utm_medium=email")
        return path + "?" + query(pairs)
    if k < 80:
        path = "/category/" + quote(CATEGORIES[rand(len(CATEGORIES))])
        pairs = ["filter=" + quote_plus("color:" + COLORS[rand(len(COLORS))])]
        if rand(2) == 0:
            pairs.append("filter=" + quote_plus("size:" + SIZES[rand(len(SIZES))]))
        if rand(3) == 0:
            pairs.append("page=%d" % (2 + rand(9)))
        return path + "?" + query(pairs)
    if k < 88:
        ids = ",".join(["%d" % (1 + rand(2000)) for _ in range(1 + rand(4))])
        return "/api/v1/items?" + query(["ids=" + quote(ids, safe=""), "fields=name%2Cprice", "token="])
    if k < 92:
        return "/login?next=" + quote_plus("/account/orders?tab=" + ("open" if rand(2) else "all"))
    return "/static/app.%x.js" % (rand(16) * 1048576 + 0x5f3a1)


def line(i: int) -> str:
    ip = "%d.%d.%d.%d" % (10 + rand(200), rand(256), rand(256), 1 + rand(254))
    t = 2 * i
    when = "%02d/%s/2026:%02d:%02d:%02d +0000" % (13 + t // 86400 % 15, MONTHS[9], t // 3600 % 24, t // 60 % 60, t % 60)
    method = "GET" if rand(10) else "POST"
    status = 200 if rand(20) else 404
    agent = AGENTS[rand(len(AGENTS))]
    return '%s - - [%s] "%s %s HTTP/1.1" %d %d "-" "%s"' % (ip, when, method, target(), status, 200 + rand(50000), agent)


def main() -> None:
    n = int(sys.argv[1])
    for i in range(n):
        print(line(i))


if __name__ == "__main__":
    main()
