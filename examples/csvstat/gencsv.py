"""gencsv: a synthetic CSV file of orders for csvstat.py, the same on every run.

usage: python3 gencsv.py N > ORDERS.csv
Each of the N rows after the header is an order: its number, date, customer, city, product,
quantity, unit price, discount, status and note, written by csv.writer in the excel dialect. Some
fields need quotes: a customer is "Last, First", some cities and products hold commas or quotes,
and a few notes span lines.
"""
import csv
import sys

FIRST = ["Ana", "Bo", "Chen", "Dmitri", "Eve", "Farah", "Grace", "Hugo", "Ines", "Jamal", "Kenji",
         "Lena", "Mateo", "Nadia", "Omar", "Priya", "Quinn", "Rosa", "Sven", "Tariq"]
LAST = ["Smith", "García", "Okafor", "Nguyen", "Müller", "Rossi", "Kowalski", "Haddad", "Silva",
        "Tanaka", "O'Brien", "Novak", "Larsen", "Dubois", "Kim"]
CITIES = ["Washington, D.C.", "Coeur d'Alene", "São Paulo", "Zürich", "Köln", "New York", "Lagos",
          "Osaka", "Lyon", "Austin", "St. John's", "Kraków"]
PRODUCTS = ['Ruler 12"', "Cable, 2 m", "Gadget", '"Deluxe" kit', "Widget", "Lamp", "Notebook A5",
            "Mug (blue)", "Charger 65 W", "Desk; oak"]
STATUSES = ["shipped", "shipped", "shipped", "delivered", "delivered", "pending", "returned",
            "cancelled"]
NOTES = ["Leave at the door", "Call first\nGate code 1234", 'Marked "fragile"', "Gift, no invoice",
         "Second floor\nRing twice\nThanks"]
DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

seed = 20261013


def rand(n: int) -> int:
    # an int in [0, n): a 31-bit linear congruential generator (glibc's constants), whose products
    # stay in 64 bits, as Pystachy's ints do
    global seed
    seed = (seed * 1103515245 + 12345) % 2147483648
    return (seed >> 8) % n


def skewed(n: int) -> int:
    # an index in [0, n), small ones far more likely: the least of three draws
    return min(rand(n), rand(n), rand(n))


def order(i: int) -> list[str]:
    # the fields of order number i
    month = rand(12)
    date = f"2026-{month + 1:02}-{rand(DAYS[month]) + 1:02}"
    customer = f"{LAST[skewed(len(LAST))]}, {FIRST[rand(len(FIRST))]}"
    quantity = 1 + skewed(20)
    price = f"{(99 + rand(20000)) / 100:.2f}"
    discount = ["", "", "", "", "0.05", "0.1", "0.15"][rand(7)]
    note = NOTES[rand(len(NOTES))] if rand(10) == 0 else ""
    return [str(i), date, customer, CITIES[skewed(len(CITIES))], PRODUCTS[skewed(len(PRODUCTS))],
            str(quantity), price, discount, STATUSES[rand(len(STATUSES))], note]


def write(n: int, f) -> None:
    # the header and n orders, to f (anything with a write() method)
    w = csv.writer(f)
    w.writerow(["order", "date", "customer", "city", "product", "quantity", "unit_price", "discount",
                "status", "note"])
    for i in range(1, n + 1):
        w.writerow(order(i))


if __name__ == "__main__":
    write(int(sys.argv[1]), sys.stdout)
