# -*- coding: utf-8 -*-
# This file is part of convertdate.
# http://github.com/fitnr/convertdate
# Licensed under the MIT license:
# http://opensource.org/licenses/MIT
# Copyright (c) 2016, 2020, 2021, 2022 fitnr <fitnr@fakeisthenewreal>
"""
The Convertdate library contains methods and functions for converting dates between
different calendar systems.

It was originally developed as as `Python Date Util <(http://sourceforge.net/projects/pythondateutil/>`__
by Phil Schwartz. It has been significantly updated and expanded.

Most of the original code is ported from
`Fourmilab's calendar converter <http://www.fourmilab.ch/documents/calendar/>`__,
which was developed by John Walker.

The algorithms are believed to be derived from: Meeus, Jean. `Astronomical Algorithms`,
Richmond: Willmann-Bell, 1991 (ISBN 0-943396-35-2)
"""
from . import (
    armenian,
    # bahai,  # Pystachy port: bahai, french_republican and persian need PyMeeus, not ported
    coptic,
    daycount,
    # dublin,  # Pystachy port: its functions are DayCount's bound methods (M2, #7; M3, #8)
    # french_republican,  # Pystachy port: PyMeeus, as bahai
    gregorian,
    hebrew,
    holidays,
    indian_civil,
    islamic,
    iso,
    julian,
    julianday,
    mayan,
    ordinal,
    # persian,  # Pystachy port: PyMeeus, as bahai
    positivist,
    utils,
)

__version__ = '2.5.1'

__all__ = [
    'armenian',
    # 'bahai',  # Pystachy port: left out above, where import * would look for it
    'coptic',
    'daycount',
    # 'dublin',  # Pystachy port: left out above, as bahai
    # 'french_republican',  # Pystachy port: left out above, as bahai
    'gregorian',
    'hebrew',
    'holidays',
    'indian_civil',
    'islamic',
    'iso',
    'julian',
    'julianday',
    'mayan',
    'ordinal',
    # 'persian',  # Pystachy port: left out above, as bahai
    'positivist',
    'utils',
]
