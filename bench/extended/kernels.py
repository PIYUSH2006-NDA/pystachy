"""Original, dependency-free workloads for Pystachy's documented Python subset.

Each public function takes a work count and returns a deterministic checksum.
Setup is included, there is no I/O, and the live data size stays bounded as the
work count grows. These are diagnostic kernels, not upstream benchmark scores.
"""


class Counter:
    def __init__(self, value: int) -> None:
        self.value = value

    def update(self, delta: int) -> int:
        self.value = (self.value + delta) % 1009
        return self.value


def object_dispatch(n: int) -> int:
    # Field loads/stores and ordinary method calls on a persistent object graph.
    counters: list[Counter] = []
    for i in range(64):
        counters.append(Counter(i))
    total = 0
    for step in range(n):
        for counter in counters:
            total += counter.update(step & 31)
    return total


def text_pipeline(n: int) -> int:
    # ASCII record parsing, temporary strings/lists, and repeated dict updates.
    records: list[str] = []
    for i in range(32):
        status = " OK " if i % 3 else " skip "
        records.append(" User" + str(i % 16) + " | " + str(i % 7 + 1) + " |" + status)
    totals: dict[str, int] = {}
    for step in range(n):
        for record in records:
            fields = record.split("|")
            name = fields[0].strip().lower()
            amount = int(fields[1].strip())
            if fields[2].strip().lower() == "ok":
                totals[name] = totals.get(name, 0) + amount
    checksum = 0
    for name in totals:
        checksum += len(name) * totals[name]
    return checksum


def list_churn(n: int) -> int:
    # Allocation, append growth, slicing/copying, extend, pop and clear/GC paths.
    checksum = 0
    for step in range(n):
        values: list[int] = []
        for i in range(256):
            values.append((i + step) & 255)
        selected = values[32:224]
        selected.extend(values[:32])
        checksum += selected.pop()
        checksum += sum(selected)
        values.clear()
        values.append(step & 255)
        checksum += values[0]
    return checksum


def exception_local(n: int) -> int:
    # One raise in eight iterations; the handler is in the raising function.
    checksum = 0
    for i in range(n):
        try:
            if i & 7 == 0:
                raise ValueError("retry")
            checksum += i & 255
        except ValueError:
            checksum += 1
    return checksum


def _maybe_raise(i: int) -> int:
    if i & 7 == 0:
        raise ValueError("retry")
    return i & 255


def exception_unwind(n: int) -> int:
    # Identical work/raise rate, with the exception crossing a function boundary.
    checksum = 0
    for i in range(n):
        try:
            checksum += _maybe_raise(i)
        except ValueError:
            checksum += 1
    return checksum


def long_string_keys(n: int) -> int:
    # Reuse the exact long key objects: expose hash caching and lookup overhead.
    prefix = "abcdefgh" * 128
    keys: list[str] = []
    values: dict[str, int] = {}
    for i in range(64):
        key = prefix + str(i)
        keys.append(key)
        values[key] = i
    checksum = 0
    for step in range(n):
        for key in keys:
            checksum += values[key]
    return checksum


class Record:
    def __init__(self, key: int, serial: int) -> None:
        self.key = key
        self.serial = serial

    def __lt__(self, other: "Record") -> bool:
        return self.key < other.key


def sort_records(n: int) -> int:
    # Timsort callbacks and object allocation; duplicate keys check stable order.
    checksum = 0
    for step in range(n):
        records: list[Record] = []
        for i in range(128):
            records.append(Record((i * 73 + step) % 31, i))
        records.sort()
        for i in range(len(records)):
            record = records[i]
            checksum += (i + 1) * (record.key + record.serial)
    return checksum
