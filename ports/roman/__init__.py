##############################################################################
#
# Copyright (c) 2001 Mark Pilgrim and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
# Pystachy port: changed for Pystachy on 2026-10-11 (ZPL clause 5); each
# change is marked "Pystachy port:", and ports/roman/PORT.md lists them.
"""Convert to and from Roman numerals"""

__author__ = "Mark Pilgrim (f8dy@diveintopython.org)"
__copyright__ = """Copyright (c) 2001 Mark Pilgrim

This program is part of "Dive Into Python", a free Python tutorial for
experienced programmers.  Visit http://diveintopython.org/ for the
latest version.
"""

# Pystachy port: `import argparse` moved into parse_args(), its only user, and
# `import re` dropped: Pystachy has neither module (#11).
import sys


# Define exceptions
class RomanError(Exception):
    pass


class OutOfRangeError(RomanError):
    pass


class NotIntegerError(RomanError):
    pass


class InvalidRomanNumeralError(RomanError):
    pass


# Define digit mapping
romanNumeralMap = (('M', 1000),
                   ('CM', 900),
                   ('D', 500),
                   ('CD', 400),
                   ('C', 100),
                   ('XC', 90),
                   ('L', 50),
                   ('XL', 40),
                   ('X', 10),
                   ('IX', 9),
                   ('V', 5),
                   ('IV', 4),
                   ('I', 1))


def toRoman(n: int) -> str:
    """convert integer to Roman numeral"""
    if not isinstance(n, int):
        raise NotIntegerError("decimals cannot be converted")
    if not (-1 < n < 5000):
        raise OutOfRangeError("number out of range (must be 0..4999)")

    # special case
    if n == 0:
        return 'N'

    result = ""
    for numeral, integer in romanNumeralMap:
        while n >= integer:
            result += numeral
            n -= integer
    return result


# Define pattern to detect valid Roman numerals
# Pystachy port: without re (#11), this function stands in for
# romanNumeralPattern.search(s), whose pattern was (in re.VERBOSE form)
#     ^M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$
# where `$` also matches before a final newline. Taking the first alternative
# that matches is enough: where another one matches too, it leaves a letter
# that the rest of the pattern cannot match, so backtracking never succeeds.
def _romanNumeralPattern_search(s: str) -> bool:
    end = len(s)
    if end > 0 and s[end - 1] == "\n":
        end -= 1
    i = 0
    count = 0
    while i < end and count < 4 and s[i] == "M":
        i += 1
        count += 1
    for one, five, ten in (("C", "D", "M"), ("X", "L", "C"), ("I", "V", "X")):
        pair = s[i:i + 2]
        if pair == one + ten or pair == one + five:
            i += 2
        else:
            if i < end and s[i] == five:
                i += 1
            count = 0
            while i < end and count < 3 and s[i] == one:
                i += 1
                count += 1
    return i == end


def fromRoman(s: str, special_case: bool = True) -> int:
    """
    Convert Roman numeral to integer.

    Parameters:
        s (str): The Roman numeral string to convert.
        special_case (bool, optional): If True (default),
            interprets 'N' as 0 for the special case of zero.

    Returns:
        int: The integer value of the Roman numeral.

    Raises:
        InvalidRomanNumeralError: If the input is not a valid Roman numeral.
    """

    if not s:
        raise InvalidRomanNumeralError('Input cannot be blank')

    s = s.upper()  # Handle lowercase inputs

    # special case
    if s == 'N' and special_case:
        return 0

    if not _romanNumeralPattern_search(s):  # Pystachy port: see above
        raise InvalidRomanNumeralError('Invalid Roman numeral: %s' % s)

    result = 0
    index = 0
    for numeral, integer in romanNumeralMap:
        while s[index:index + len(numeral)] == numeral:
            result += integer
            index += len(numeral)
    return result


def parse_args() -> "argparse.Namespace":  # Pystachy port: quoted
    import argparse  # Pystachy port: moved from the module level
    parser = argparse.ArgumentParser(
        prog='roman',
        description='convert between roman and arabic numerals'
    )
    parser.add_argument('number', help='the value to convert')
    parser.add_argument(
        '-r', '--reverse',
        action='store_true',
        default=False,
        help='convert roman to numeral (case insensitive) [default: False]')

    args = parser.parse_args()
    args.number = args.number
    return args


def main() -> int:
    args = parse_args()
    if args.reverse:
        r = fromRoman(args.number)
        print(r)
    else:
        i = int(args.number)
        n = toRoman(i)
        print(n)

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())  # pragma: no cover
