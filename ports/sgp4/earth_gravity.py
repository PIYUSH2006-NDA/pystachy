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

# Pystachy port: EarthGravity(*getgravconst(...)) with the eight items passed one by one (star
# arguments, M3)
_g = getgravconst('wgs72old')
wgs72old = EarthGravity(_g[0], _g[1], _g[2], _g[3], _g[4], _g[5], _g[6], _g[7])
_g = getgravconst('wgs72')
wgs72 = EarthGravity(_g[0], _g[1], _g[2], _g[3], _g[4], _g[5], _g[6], _g[7])
_g = getgravconst('wgs84')
wgs84 = EarthGravity(_g[0], _g[1], _g[2], _g[3], _g[4], _g[5], _g[6], _g[7])
