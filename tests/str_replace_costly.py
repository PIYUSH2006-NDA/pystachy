# str.replace where the occurrences are dense but their search is costly (issue #36's review): a
# needle whose first byte is common where the needle is not, as "CA" in random text over ACG. The
# runtime counts the rest of a dense text only where its failed candidates cost no more than the
# bytes they pass; otherwise it lists them, as for sparse ones, and searches the text once. Either
# way the result is the text's split on the needle, joined with the replacement.
CAP = 65536


def dna(k: int, reps: int) -> str:
    # random text over the first k letters of ACGT, as an LCG gives it: 400,000 bytes, reps times
    x = 28
    parts: list[str] = []
    for i in range(100000):
        x = (x * 1103515245 + 12345) % 2147483648
        parts.append("ACGT"[x % k] + "ACGT"[(x >> 8) % k] + "ACGT"[(x >> 16) % k] + "ACGT"[(x >> 24) % k])
    return "".join(parts) * reps


def check(tag: str, s: str, old: str, new: str, counts: list[int]) -> None:
    for count in counts:
        r = s.replace(old, new, count)
        want = new.join(s.split(old, count))
        # (lengths and slices only of ASCII text: Pystachy's count bytes)
        print(tag, count, s.count(old), r == want)
        if r.isascii():
            print(" ", len(r), repr(r[:12]), repr(r[-12:]))


acg = dna(3, 3)
check("acg", acg, "CA", "#", [-1, CAP, CAP + 1, 100000])
check("acg-long", acg, "CA", "<ca>", [-1])
acgt = dna(4, 6)
check("acgt", acgt, "GA", "", [-1, CAP + 1])
check("acgt-3", acgt, "GAC", "x", [-1])
# a dense prefix, then a long run of failed candidates, then the needle once more: a count that
# ends in the prefix needs no count of the run
for old in ["ab", "a" * 15 + "b"]:
    s = old * 70000 + "a" * 300000 + old
    check("prefix" + str(len(old)), s, old, "", [-1, CAP + 1, 70000, 70001])
# dense, costly, then dense again; and failed candidates cheap enough to count past
s = "ab" * 70000 + ("a" * 40 + "ab") * 3000 + "ab" * 100000
check("dense-costly-dense", s, "ab", "Z", [-1, CAP + 1, 140000])
s = ("ab" + "y" * 13 + "ab" + "y" * 12 + "a") * 70000
check("cheap-fails", s, "ab", "-", [-1, CAP + 1, 70001])
# non-ASCII: a 2-byte needle whose first byte begins most characters of the text
s = ("éè" * 3 + "ê") * 40000
check("e-accents", s, "éè", "e", [-1, CAP + 1])
