"""gendata: synthetic customer records for mailmerge.py, the same on every run.

usage: python3 gendata.py N > DATA
DATA is a header line that names the fields, then N records, one per line, with the fields
separated by tabs: a customer's name, email, account number, plan, the amount due, the date the
plan renews and the last four digits of a card, drawn from a linear congruential generator.
"""
import sys

FIRST = ["Ada", "Alan", "Barbara", "Claude", "Dennis", "Edsger", "Frances", "Grace", "Guido",
         "Hedy", "Ivan", "Jean", "John", "Ken", "Leslie", "Linus", "Margaret", "Niklaus",
         "Radia", "Tim"]
LAST = ["Lovelace", "Turing", "Liskov", "Shannon", "Ritchie", "Dijkstra", "Allen", "Hopper",
        "van Rossum", "Lamarr", "Sutherland", "Sammet", "McCarthy", "Thompson", "Lamport",
        "Torvalds", "Hamilton", "Wirth", "Perlman", "Berners-Lee"]
PLANS = ["Basic", "Standard", "Premium", "Team"]
PRICES = [499, 999, 1999, 4999]  # cents
FIELDS = ["name", "email", "account", "plan", "amount", "due", "card"]

seed = 20261013


def rand(n: int) -> int:
    # an int in [0, n): a 31-bit linear congruential generator (glibc's constants), whose products
    # stay in 64 bits, as Pystachy's ints do
    global seed
    seed = (seed * 1103515245 + 12345) % 2147483648
    return (seed >> 8) % n


def record(i: int) -> list[str]:
    # the fields of record i
    first = FIRST[rand(len(FIRST))]
    last = LAST[rand(len(LAST))]
    plan = rand(len(PLANS))
    months = 1 + rand(12) // 9 * 11  # a quarter of them pay for a year
    cents = PRICES[plan] * months
    email = f"{first.lower()}.{last.lower().replace(' ', '')}{i % 97}@example.com"
    return [f"{first} {last}", email, f"{100000 + i * 7919 % 900000}", PLANS[plan],
            f"{cents // 100}.{cents % 100:02}", f"2026-{11 + rand(2)}-{1 + rand(28):02}",
            f"{rand(10000):04}"]


def main() -> None:
    n = int(sys.argv[1])
    print("\t".join(FIELDS))
    for i in range(n):
        print("\t".join(record(i)))


if __name__ == "__main__":
    main()
