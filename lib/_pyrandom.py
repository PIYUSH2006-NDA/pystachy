"""The _random module's Mersenne Twister generator, written for Pystachy.

CPython's _random is a C module, Modules/_randommodule.c; this one follows that file of CPython
3.13.16 (lib/provenance.md): init_genrand(), init_by_array(), genrand_uint32() and the methods of
_random.Random, with the C code's operations in its order, so a seeded generator gives the values
CPython's does. Its uint32_t arithmetic is done in checked 64-bit ints: each product of two 32-bit
words has a factor below 2**31, and stays below 2**63, and each result is masked to 32 bits.

lib/random.py's Random derives from this Random, as CPython's derives from the C type.
"""

# The generator follows the MT19937 reference code, whose comments CPython's _randommodule.c keeps:
#
# A C-program for MT19937, with initialization improved 2002/1/26.
# Coded by Takuji Nishimura and Makoto Matsumoto.
#
# Before using, initialize the state by using init_genrand(seed)
# or init_by_array(init_key, key_length).
#
# Copyright (C) 1997 - 2002, Makoto Matsumoto and Takuji Nishimura,
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#
#  3. The names of its contributors may not be used to endorse or promote
#     products derived from this software without specific prior written
#     permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from math import frexp as _frexp, isfinite as _isfinite, isinf as _isinf
import os as _os
import time as _time

# Period parameters
_N = 624
_M = 397
_MATRIX_A = 0x9908b0df  # constant vector a
_UPPER_MASK = 0x80000000  # most significant w-r bits
_LOWER_MASK = 0x7fffffff  # least significant r bits


class Random:
    """Random() -> create a random number generator with its own internal state."""

    _state: list[int]  # the N words of uint32_t state
    _index: int

    def __init__(self, n: int | float | bool | None = None) -> None:
        self._state = [0] * _N
        self._index = 0
        self.seed(n)

    def _genrand_uint32(self) -> int:
        # genrand_uint32(): generates a random number on [0,0xffffffff]-interval
        mt = self._state
        if self._index >= _N:  # generate N words at one time
            kk = 0
            while kk < _N - _M:
                y = (mt[kk] & _UPPER_MASK) | (mt[kk + 1] & _LOWER_MASK)
                mt[kk] = mt[kk + _M] ^ (y >> 1) ^ (_MATRIX_A if y & 0x1 else 0)
                kk += 1
            while kk < _N - 1:
                y = (mt[kk] & _UPPER_MASK) | (mt[kk + 1] & _LOWER_MASK)
                mt[kk] = mt[kk + (_M - _N)] ^ (y >> 1) ^ (_MATRIX_A if y & 0x1 else 0)
                kk += 1
            y = (mt[_N - 1] & _UPPER_MASK) | (mt[0] & _LOWER_MASK)
            mt[_N - 1] = mt[_M - 1] ^ (y >> 1) ^ (_MATRIX_A if y & 0x1 else 0)
            self._index = 0

        y = mt[self._index]
        self._index += 1
        y ^= y >> 11
        y ^= (y << 7) & 0x9d2c5680
        y ^= (y << 15) & 0xefc60000
        y ^= y >> 18
        return y

    def random(self) -> float:
        """random() -> x in the interval [0, 1)."""
        # random_random() is the same as genrand_res53() from the reference code
        a = self._genrand_uint32() >> 5
        b = self._genrand_uint32() >> 6
        return (a * 67108864.0 + b) * (1.0 / 9007199254740992.0)

    def _init_genrand(self, s: int) -> None:
        # initializes mt[N] with a seed: in a new list, as lib/random.py's Random.__init__() does
        # not call this __init__() (the C type's state is made with the object)
        mt = [0] * _N
        self._state = mt
        mt[0] = s
        for mti in range(1, _N):
            # 1812433253 * (2**32 - 1) + 623 < 2**63
            mt[mti] = (1812433253 * (mt[mti - 1] ^ (mt[mti - 1] >> 30)) + mti) & 0xffffffff
        self._index = _N

    def _init_by_array(self, init_key: list[int]) -> None:
        # initialize by an array: init_key is the array for initializing keys
        key_length = len(init_key)
        self._init_genrand(19650218)
        mt = self._state
        i = 1
        j = 0
        k = _N if _N > key_length else key_length
        while k:
            mt[i] = ((mt[i] ^ ((mt[i - 1] ^ (mt[i - 1] >> 30)) * 1664525))
                     + init_key[j] + j) & 0xffffffff  # non linear
            i += 1
            j += 1
            if i >= _N:
                mt[0] = mt[_N - 1]
                i = 1
            if j >= key_length:
                j = 0
            k -= 1
        k = _N - 1
        while k:
            # (2**32 - 1) * 1566083941 < 2**63; a negative difference is masked as C wraps it
            mt[i] = ((mt[i] ^ ((mt[i - 1] ^ (mt[i - 1] >> 30)) * 1566083941))
                     - i) & 0xffffffff  # non linear
            i += 1
            if i >= _N:
                mt[0] = mt[_N - 1]
                i = 1
            k -= 1

        mt[0] = 0x80000000  # MSB is 1; assuring non-zero initial array

    def _seed_time_pid(self) -> None:
        # random_seed_time_pid(), C's fallback where the system's entropy cannot be read, as
        # Pystachy's is not (it has no os.urandom()): the time, the process id and the
        # monotonic clock, each in 32-bit words
        now = _time.time_ns()
        mono = _time.monotonic_ns()
        self._init_by_array([now & 0xffffffff, (now >> 32) & 0xffffffff, _os.getpid() & 0xffffffff,
                             mono & 0xffffffff, (mono >> 32) & 0xffffffff])

    def seed(self, n=None, /) -> None:
        """seed([n]) -> None.

        Defaults to use urandom and falls back to a combination
        of the current time and the process identifier.
        """
        # random_seed(): None seeds from the time and process id (above); an int seeds with the
        # 32-bit words of its absolute value, from the right, and a float with those of its
        # hash, cast to an unsigned size_t
        if n is None:
            self._seed_time_pid()
            return
        if isinstance(n, float):
            h = _hash_float(n)
            if h < 0:  # (size_t)hash: 64 bits
                key = [h & 0xffffffff, (h >> 32) & 0xffffffff]
            else:
                key = _key_words(h)
        elif isinstance(n, bool):
            key = [1 if n else 0]  # int.__abs__() of a bool
        elif n < 0:
            if n == -0x7fffffffffffffff - 1:  # abs() of -2**63
                key = [0, 0x80000000]
            else:
                key = _key_words(-n)
        else:
            key = _key_words(n)
        self._init_by_array(key)

    def getstate(self) -> tuple[int, ...]:
        """getstate() -> tuple containing the current state."""
        state = self._state[:]
        state.append(self._index)
        return tuple(state)

    def setstate(self, state: tuple[int, ...]) -> None:
        """setstate(state) -> None.  Restores generator state."""
        if len(state) != _N + 1:
            raise ValueError("state vector is the wrong size")
        new_state = [0] * _N
        for i in range(_N):
            element = state[i]
            if element < 0:  # PyLong_AsUnsignedLong()
                raise OverflowError("can't convert negative value to unsigned int")
            new_state[i] = element & 0xffffffff
        index = state[_N]
        if index < 0 or index > _N:
            raise ValueError("invalid state")
        self._index = index
        self._state = new_state

    def getrandbits(self, k: int) -> int:
        """getrandbits(k) -> x.  Generates an int with k random bits."""
        if k < 0:
            raise ValueError("number of bits must be non-negative")

        if k == 0:
            return 0

        if k <= 32:  # Fast path
            return self._genrand_uint32() >> (32 - k)

        # Pystachy's ints have 64 bits: two 32-bit words, from least significant to most
        # significant, hold up to 63 random bits
        if k > 63:
            raise OverflowError("integer result does not fit in 64 bits")
        r = self._genrand_uint32()
        return r | ((self._genrand_uint32() >> (64 - k)) << 32)


def _key_words(n: int) -> list[int]:
    # the 32-bit words of n >= 0, from the right: one word for 0
    key = [n & 0xffffffff]
    n >>= 32
    while n:
        key.append(n & 0xffffffff)
        n >>= 32
    return key


_PyHASH_BITS = 61
_PyHASH_MODULUS = (1 << _PyHASH_BITS) - 1
_PyHASH_INF = 314159


def _hash_float(v: float) -> int:
    # _Py_HashDouble() of Python/pyhash.c: hash(v), for a float v. Its unsigned operations are done
    # below 2**61: a shift left first drops the bits the modulus mask would drop.
    if not _isfinite(v):
        if _isinf(v):
            return _PyHASH_INF if v > 0 else -_PyHASH_INF
        # a NaN's hash is its object's address, which a Pystachy float has not: 0 here
        return 0
    m, e = _frexp(v)
    sign = 1
    if m < 0:
        sign = -1
        m = -m
    # process 28 bits at a time
    x = 0
    while m:
        x = ((x & ((1 << (_PyHASH_BITS - 28)) - 1)) << 28) | x >> (_PyHASH_BITS - 28)
        m *= 268435456.0  # 2**28
        e -= 28
        y = int(m)  # pull out integer part
        m -= y
        x += y
        if x >= _PyHASH_MODULUS:
            x -= _PyHASH_MODULUS
    # adjust for the exponent; first reduce it modulo _PyHASH_BITS
    e = e % _PyHASH_BITS if e >= 0 else _PyHASH_BITS - 1 - ((-1 - e) % _PyHASH_BITS)
    x = ((x & ((1 << (_PyHASH_BITS - e)) - 1)) << e) | x >> (_PyHASH_BITS - e)
    x = x * sign
    if x == -1:
        x = -2
    return x
