"""Three earth-gravity models for use with SGP4."""

from typing import NamedTuple  # Pystachy port: for EarthGravity, below
from sgp4.propagation import getgravconst

# Pystachy port: collections.namedtuple (not a Pystachy module, #11) as the same typing.NamedTuple
class EarthGravity(NamedTuple):
    tumin: float
    mu: float
    radiusearthkm: float
    xke: float
    j2: float
    j3: float
    j4: float
    j3oj2: float

wgs72old = EarthGravity(*getgravconst('wgs72old'))
wgs72 = EarthGravity(*getgravconst('wgs72'))
wgs84 = EarthGravity(*getgravconst('wgs84'))
