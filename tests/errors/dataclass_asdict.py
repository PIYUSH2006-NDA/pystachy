# error: dataclasses.asdict is not supported
from dataclasses import asdict, dataclass


@dataclass
class P:
    x: int


print(asdict(P(1)))
