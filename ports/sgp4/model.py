"""The Satellite class."""

from sgp4.alpha5 import from_alpha5
from sgp4.earth_gravity import wgs72old, wgs72, wgs84
from sgp4.ext import invjday, jday
from sgp4.io import twoline2rv
from sgp4.propagation import sgp4, sgp4init

WGS72OLD = 0
WGS72 = 1
WGS84 = 2
# Pystachy port: a list, as only a constant indexes a tuple (tuples indexed by a variable, M1)
gravity_constants = [wgs72old, wgs72, wgs84]  # indexed using enum values above
minutes_per_day = 1440.

class Satrec(object):
    """Slow Python-only version of the satellite object."""

    # Approximate the behavior of the C-accelerated class by locking
    # down attribute access, to avoid folks accidentally writing code
    # against this class and adding extra attributes, then moving to a
    # computer where the C-accelerated class is used and having their
    # code suddenly produce errors.
    __slots__ = (
        'Om', 'a', 'alta', 'altp', 'am', 'argpdot', 'argpo', 'atime', 'aycof',
        'bstar', 'cc1', 'cc4', 'cc5', 'classification', 'con41', 'd2', 'd2201',
        'd2211', 'd3', 'd3210', 'd3222', 'd4', 'd4410', 'd4422', 'd5220',
        'd5232', 'd5421', 'd5433', 'dedt', 'del1', 'del2', 'del3', 'delmo',
        'didt', 'dmdt', 'dnodt', 'domdt', 'e3', 'ecco', 'ee2', 'elnum', 'em',
        'ephtype', 'epoch', 'epochdays', 'epochyr', 'error', 'error_message',
        'eta', 'gsto', 'im', 'inclo', 'init', 'intldesg', 'irez', 'isimp',
        'j2', 'j3', 'j3oj2', 'j4', 'jdsatepoch', 'mdot', 'method', 'mm', 'mo',
        'mu', 'nddot', 'ndot', 'nm', 'no_kozai', 'no_unkozai', 'nodecf',
        'nodedot', 'nodeo', 'om', 'omgcof', 'operationmode', 'peo', 'pgho',
        'pho', 'pinco', 'plo', 'radiusearthkm', 'revnum', 'satnum_str', 'se2',
        'se3', 'sgh2', 'sgh3', 'sgh4', 'sh2', 'sh3', 'si2', 'si3', 'sinmao',
        'sl2', 'sl3', 'sl4', 't', 't2cof', 't3cof', 't4cof', 't5cof', 'tumin',
        'x1mth2', 'x7thm1', 'xfact', 'xgh2', 'xgh3', 'xgh4',
        'xh2', 'xh3', 'xi2', 'xi3', 'xke', 'xl2', 'xl3', 'xl4', 'xlamo',
        'xlcof', 'xli', 'xmcof', 'xni', 'zmol', 'zmos',
        'jdsatepochF'
    )

    # Pystachy port: the slots' types are annotated, but epoch's (see io.py): Pystachy types a
    # field from the class body or __init__ only, and the module functions twoline2rv() and
    # sgp4init() assign these (M2).
    Om: float
    a: float
    alta: float
    altp: float
    am: float
    argpdot: float
    argpo: float
    atime: float
    aycof: float
    bstar: float
    cc1: float
    cc4: float
    cc5: float
    classification: str
    con41: float
    d2: float
    d2201: float
    d2211: float
    d3: float
    d3210: float
    d3222: float
    d4: float
    d4410: float
    d4422: float
    d5220: float
    d5232: float
    d5421: float
    d5433: float
    dedt: float
    del1: float
    del2: float
    del3: float
    delmo: float
    didt: float
    dmdt: float
    dnodt: float
    domdt: float
    e3: float
    ecco: float
    ee2: float
    elnum: int
    em: float
    ephtype: int
    epochdays: float
    epochyr: int
    error: int
    error_message: str | None
    eta: float
    gsto: float
    im: float
    inclo: float
    init: str
    intldesg: str
    irez: int
    isimp: int
    j2: float
    j3: float
    j3oj2: float
    j4: float
    jdsatepoch: float
    mdot: float
    method: str
    mm: float
    mo: float
    mu: float
    nddot: float
    ndot: float
    nm: float
    no_kozai: float
    no_unkozai: float
    nodecf: float
    nodedot: float
    nodeo: float
    om: float
    omgcof: float
    operationmode: str
    peo: float
    pgho: float
    pho: float
    pinco: float
    plo: float
    radiusearthkm: float
    revnum: int
    satnum_str: str
    se2: float
    se3: float
    sgh2: float
    sgh3: float
    sgh4: float
    sh2: float
    sh3: float
    si2: float
    si3: float
    sinmao: float
    sl2: float
    sl3: float
    sl4: float
    t: float
    t2cof: float
    t3cof: float
    t4cof: float
    t5cof: float
    tumin: float
    x1mth2: float
    x7thm1: float
    xfact: float
    xgh2: float
    xgh3: float
    xgh4: float
    xh2: float
    xh3: float
    xi2: float
    xi3: float
    xke: float
    xl2: float
    xl3: float
    xl4: float
    xlamo: float
    xlcof: float
    xli: float
    xmcof: float
    xni: float
    zmol: float
    zmos: float
    jdsatepochF: float

    # Pystachy port: array, which only sgp4_array() (NumPy) uses, is left out with it (a class
    # attribute that is None, M2)
    # array = None       # replaced, if needed, with NumPy array()

    def __init__(self):
        self.revnum = 0  # for consistency, since sgp4init() leaves this unset

    # Pystachy port: the properties' return types are annotated (a property needs one, M2)
    @property
    def no(self) -> float:
        return self.no_kozai

    @property
    def satnum(self) -> int:
        return from_alpha5(self.satnum_str)

    @classmethod
    def twoline2rv(cls, line1, line2, whichconst=WGS72):
        whichconst = gravity_constants[whichconst]
        self = cls()
        twoline2rv(line1, line2, whichconst, 'i', self)

        # Expose the same attribute types as the C++ code.
        # Pystachy port: io.twoline2rv() ends with these two conversions (a field has one type, M4)
        # self.ephtype = int(self.ephtype.strip() or '0')
        # self.revnum = int(self.revnum)

        # Install a fancy split JD of the kind the C++ natively supports.
        # We rebuild it from the TLE year and day to maintain precision.
        year = self.epochyr
        days, fraction = divmod(self.epochdays, 1.0)
        self.jdsatepoch = year * 365 + (year - 1) // 4 + days + 1721044.5
        self.jdsatepochF = round(fraction, 8)  # exact number of digits in TLE

        # Remove the legacy datetime "epoch", which is not provided by
        # the C++ version of the object.
        # Pystachy port: io.twoline2rv() does not set it (datetime, #11)
        # del self.epoch

        # Undo my non-standard 4-digit year
        self.epochyr %= 100
        return self

    def sgp4init(self, whichconst, opsmode, satnum, epoch, bstar,
                 ndot, nddot, ecco, argpo, inclo, mo, no_kozai, nodeo):
        whichconst = gravity_constants[whichconst]
        whole, fraction = divmod(epoch, 1.0)
        whole_jd = whole + 2433281.5

        # Go out on a limb: if `epoch` has no decimal digits past the 8
        # decimal places stored in a TLE, then assume the user is trying
        # to specify an exact decimal fraction.
        if round(epoch, 8) == epoch:
            fraction = round(fraction, 8)

        self.jdsatepoch = whole_jd
        self.jdsatepochF = fraction

        y, m, d, H, M, S = invjday(whole_jd)
        jan0 = jday(y, 1, 0, 0, 0, 0.0)
        self.epochyr = y % 100
        self.epochdays = whole_jd - jan0 + fraction

        self.classification = 'U'

        sgp4init(whichconst, opsmode, satnum, epoch, bstar, ndot, nddot,
                 ecco, argpo, inclo, mo, no_kozai, nodeo, self)

    def sgp4(self, jd, fr):
        tsince = ((jd - self.jdsatepoch) * minutes_per_day +
                  (fr - self.jdsatepochF) * minutes_per_day)
        r, v = sgp4(self, tsince)
        return self.error, r, v

    def sgp4_tsince(self, tsince):
        r, v = sgp4(self, tsince)
        return self.error, r, v

    # Pystachy port: sgp4_array(), which takes and returns NumPy arrays, is left out (NumPy)
    # def sgp4_array(self, jd, fr):
    #     """Compute positions and velocities for the times in a NumPy array.
    #
    #     Given NumPy arrays ``jd`` and ``fr`` of the same length that
    #     supply the whole part and the fractional part of one or more
    #     Julian dates, return a tuple ``(e, r, v)`` of three vectors:
    #
    #     * ``e``: nonzero for any dates that produced errors, 0 otherwise.
    #     * ``r``: position vectors in kilometers.
    #     * ``v``: velocity vectors in kilometers per second.
    #
    #     """
    #     # Import NumPy the first time sgp4_array() is called.
    #     array = self.array
    #     if array is None:
    #         from numpy import array
    #         Satrec.array = array
    #
    #     results = []
    #     z = list(zip(jd, fr))
    #     for jd_i, fr_i in z:
    #         results.append(self.sgp4(jd_i, fr_i))
    #     elist, rlist, vlist = zip(*results)
    #
    #     e = array(elist)
    #     r = array(rlist)
    #     v = array(vlist)
    #
    #     r.shape = v.shape = len(jd), 3
    #     return e, r, v

class SatrecArray(object):
    """Slow Python-only version of the satellite array."""

    __slots__ = ('_satrecs',)

    array = None  # replaced with NumPy array(), if the user tries calling

    def __init__(self, satrecs):
        self._satrecs = satrecs
        # Import NumPy the first time a SatrecArray is instantiated.
        if self.array is None:
            from numpy import array
            SatrecArray.array = array

    def sgp4(self, jd, fr):
        """Compute positions and velocities for the satellites in this array.

        Given NumPy scalars or arrays ``jd`` and ``fr`` supplying the
        whole part and the fractional part of one or more Julian dates,
        return a tuple ``(e, r, v)`` of three vectors that are each as
        long as ``jd`` and ``fr``:

        * ``e``: nonzero for any dates that produced errors, 0 otherwise.
        * ``r``: (x,y,z) position vector in kilometers.
        * ``v``: (dx,dy,dz) velocity vector in kilometers per second.

        """
        results = []
        z = list(zip(jd, fr))
        for satrec in self._satrecs:
            for jd_i, fr_i in z:
                results.append(satrec.sgp4(jd_i, fr_i))
        elist, rlist, vlist = zip(*results)

        e = self.array(elist)
        r = self.array(rlist)
        v = self.array(vlist)

        jdlen = len(jd)
        mylen = len(self._satrecs)
        e.shape = (mylen, jdlen)
        r.shape = v.shape = (mylen, jdlen, 3)

        return e, r, v

class Satellite(object):
    """The old Satellite object, for compatibility with sgp4 1.x."""
    jdsatepochF = 0.0  # for compatibility with new Satrec; makes tests simpler

    def propagate(self, year, month=1, day=1, hour=0, minute=0, second=0.0):
        """Return a position and velocity vector for a given date and time."""

        j = jday(year, month, day, hour, minute, second)
        m = (j - self.jdsatepoch) * minutes_per_day
        r, v = sgp4(self, m)
        return r, v

    # Pystachy port: the legacy class's copies of Satrec's two properties are left out (a class
    # attribute read from another class, and properties, M2)
    # no = Satrec.no
    # satnum = Satrec.satnum
