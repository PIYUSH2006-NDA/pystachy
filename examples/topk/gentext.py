"""gentext: a synthetic text for topk.py, the same on every run.

usage: python3 gentext.py WORDS > TEXT
Its words follow Zipf's law, as a language's do: the word of rank r comes up about 1/(r + 1) times
as often as the commonest, drawn with integers alone (a band of ranks [2**b - 1, 2**(b+1) - 1) with
b uniform, then a rank of the band) from a linear congruential generator. The 48 commonest words
are English's; the others are made of syllables, the commoner the shorter. Each line is a
sentence of 4 to 19 words, capitalized, with a comma after about one word in eight.
"""
import sys

COMMON = ["the", "of", "and", "to", "a", "in", "is", "it", "you", "that", "he", "was", "for", "on",
          "are", "with", "as", "his", "they", "be", "at", "one", "have", "this", "from", "or", "had",
          "by", "not", "word", "but", "what", "some", "we", "can", "out", "other", "were", "all",
          "there", "when", "up", "use", "your", "how", "said", "an", "each"]
SYLLABLES = ["ka", "lo", "mi", "ne", "ru", "sa", "ti", "vo", "da", "fe", "gu", "ji", "pe", "zo",
             "xi", "qu"]
BANDS = 17  # ranks 0 to 2**17 - 2

seed = 20261013


def rand(n: int) -> int:
    # an int in [0, n): a 31-bit linear congruential generator (glibc's constants), whose products
    # stay in 64 bits, as Pystachy's ints do
    global seed
    seed = (seed * 1103515245 + 12345) % 2147483648
    return (seed >> 8) % n


def word(r: int) -> str:
    # the word of rank r: an English one, else r's digits in bijective base 16, a syllable each
    if r < len(COMMON):
        return COMMON[r]
    k = r - len(COMMON) + 1
    w = ""
    while k > 0:
        k -= 1
        w += SYLLABLES[k % len(SYLLABLES)]
        k //= len(SYLLABLES)
    return w


def rank() -> int:
    # a rank, r with a probability of about 1 / (BANDS * (r + 1))
    b = rand(BANDS)
    return (1 << b) - 1 + rand(1 << b)


def sentence() -> str:
    words = [word(rank()) for _ in range(4 + rand(16))]
    for i in range(len(words) - 1):
        if rand(8) == 0:
            words[i] += ","
    return " ".join(words).capitalize() + "."


def main() -> None:
    n = int(sys.argv[1])
    total = 0
    while total < n:
        s = sentence()
        total += s.count(" ") + 1
        print(s)


if __name__ == "__main__":
    main()
