"""Filename matching with shell patterns.

fnmatch(FILENAME, PATTERN) matches according to the local convention.
fnmatchcase(FILENAME, PATTERN) always takes case in account.

The functions operate by translating the pattern into a regular
expression.  They cache the compiled regular expressions for speed.

The function translate(PATTERN) returns a regular expression
corresponding to PATTERN.  (It does not compile it.)
"""
# Pystachy port: CPython 3.13.16's Lib/fnmatch.py, edited where marked (lib/README.md)
import os
import posixpath
import re
import functools
from typing import Callable  # Pystachy port: for _compile_pattern's annotation

__all__ = ["filter", "fnmatch", "fnmatchcase", "translate"]

# Pystachy port: range endpoints are characters, while a str's indices count UTF-8 bytes.
_UTF8 = len("é") == 2


def _next_char(s: str, i: int) -> int:
    if not _UTF8 or i >= len(s):
        return i + 1
    b = ord(s[i])
    # Pystachy port: use re._codes()'s byte fallback for incomplete/invalid UTF-8, an overlong
    # form or a value past U+10FFFF (re._charat()).
    if b < 0xC2 or b >= 0xF5:
        return i + 1
    width = 2 if b < 0xE0 else 3 if b < 0xF0 else 4
    if i + width > len(s):
        return i + 1
    x = ord(s[i + 1])
    if x & 0xC0 != 0x80 or (b == 0xE0 and x < 0xA0) or (b == 0xF0 and x < 0x90) or (b == 0xF4 and x >= 0x90):
        return i + 1
    for j in range(2, width):
        if ord(s[i + j]) & 0xC0 != 0x80:
            return i + 1
    return i + width


def _last_char(s: str) -> int:
    i = len(s) - 1
    if _UTF8:
        # A trailing continuation belongs to a character only when its complete sequence
        # reaches the end; otherwise it is one standalone byte, just as in _next_char().
        for start in range(max(0, i - 3), i):
            if _next_char(s, start) == len(s):
                return start
    return i


def _char_value(s: str) -> int:
    # Pystachy port: raw bytes and UTF-8 endpoints compare by re._codes()'s value, not bytes.
    value = ord(s[0])
    if _UTF8 and len(s) > 1:
        value &= 0x1F if len(s) == 2 else 0x0F if len(s) == 3 else 0x07
        for i in range(1, len(s)):
            value = (value << 6) | (ord(s[i]) & 0x3F)
    return value


def fnmatch(name, pat):
    """Test whether FILENAME matches PATTERN.

    Patterns are Unix shell style:

    *       matches everything
    ?       matches any single character
    [seq]   matches any character in seq
    [!seq]  matches any char not in seq

    An initial period in FILENAME is not special.
    Both FILENAME and PATTERN are first case-normalized
    if the operating system requires it.
    If you don't want this, use fnmatchcase(FILENAME, PATTERN).
    """
    name = os.path.normcase(name)
    pat = os.path.normcase(pat)
    return fnmatchcase(name, pat)

@functools.lru_cache(maxsize=32768, typed=True)
def _compile_pattern(pat: str) -> Callable[[str], re.Match | None]:  # Pystachy port: annotated (str patterns only)
    if isinstance(pat, bytes):
        pat_str = str(pat, 'ISO-8859-1')
        res_str = translate(pat_str)
        res = bytes(res_str, 'ISO-8859-1')
    else:
        res = translate(pat)
    return re.compile(res).match

def filter(names, pat):
    """Construct a list from those elements of the iterable NAMES that match PAT."""
    result = []
    pat = os.path.normcase(pat)
    match = _compile_pattern(pat)
    if os.name == 'posix':  # Pystachy port: for os.path is posixpath (a module is no value here)
        # normcase on posix is NOP. Optimize it away from the loop.
        for name in names:
            if match(name):
                result.append(name)
    else:
        for name in names:
            if match(os.path.normcase(name)):
                result.append(name)
    return result

def fnmatchcase(name, pat):
    """Test whether FILENAME matches PATTERN, including case.

    This is a version of fnmatch() which doesn't case-normalize
    its arguments.
    """
    match = _compile_pattern(pat)
    return match(name) is not None


def translate(pat):
    """Translate a shell PATTERN to a regular expression.

    There is no way to quote meta-characters.
    """

    STAR = None  # Pystachy port: for object(), which has no type (#251): None is no str item either
    parts = _translate(pat, STAR, '.')
    return _join_translated_parts(parts, STAR)


def _translate(pat, STAR, QUESTION_MARK):
    res: list[str | None] = []  # Pystachy port: annotated, for the str items and STAR
    add = res.append
    i, n = 0, len(pat)
    while i < n:
        c = pat[i]
        i = i+1
        if c == '*':
            # compress consecutive `*` into one
            if (not res) or res[-1] is not STAR:
                add(STAR)
        elif c == '?':
            add(QUESTION_MARK)
        elif c == '[':
            j = i
            if j < n and pat[j] == '!':
                j = j+1
            if j < n and pat[j] == ']':
                j = j+1
            while j < n and pat[j] != ']':
                j = j+1
            if j >= n:
                add('\\[')
            else:
                stuff = pat[i:j]
                if '-' not in stuff:
                    stuff = stuff.replace('\\', r'\\')
                else:
                    chunks = []
                    # Pystachy port: skip whole characters when finding each range.
                    k = _next_char(pat, i+1 if pat[i] == '!' else i)
                    while True:
                        k = pat.find('-', k, j)
                        if k < 0:
                            break
                        chunks.append(pat[i:k])
                        i = k+1
                        k = _next_char(pat, _next_char(pat, i))
                    chunk = pat[i:j]
                    if chunk:
                        chunks.append(chunk)
                    else:
                        chunks[-1] += '-'
                    # Remove empty ranges -- invalid in RE.
                    for k in range(len(chunks)-1, 0, -1):
                        # Pystachy port: compare and remove complete range endpoints.
                        left, right = chunks[k-1], chunks[k]
                        last, first = _last_char(left), _next_char(right, 0)
                        if _char_value(left[last:]) > _char_value(right[:first]):
                            chunks[k-1] = left[:last] + right[first:]
                            del chunks[k]
                    # Escape backslashes and hyphens for set difference (--).
                    # Hyphens that create ranges shouldn't be escaped.
                    stuff = '-'.join(s.replace('\\', r'\\').replace('-', r'\-')
                                     for s in chunks)
                # Escape set operations (&&, ~~ and ||).
                # Pystachy port: three literal escapes avoid invoking the regex matcher.
                if '&' in stuff:
                    stuff = stuff.replace('&', r'\&')
                if '~' in stuff:
                    stuff = stuff.replace('~', r'\~')
                if '|' in stuff:
                    stuff = stuff.replace('|', r'\|')
                i = j+1
                if not stuff:
                    # Empty range: never match.
                    add('(?!)')
                elif stuff == '!':
                    # Negated empty range: match any character.
                    add('.')
                else:
                    if stuff[0] == '!':
                        stuff = '^' + stuff[1:]
                    elif stuff[0] in ('^', '['):
                        stuff = '\\' + stuff
                    add(f'[{stuff}]')
        else:
            add(re.escape(c))
    assert i == n
    return res


def _join_translated_parts(inp, STAR):
    # Deal with STARs.
    res: list[str | None] = []  # Pystachy port: annotated, as add() reads it before its first item
    add = res.append
    i, n = 0, len(inp)
    # Fixed pieces at the start?
    while i < n and inp[i] is not STAR:
        add(inp[i])
        i += 1
    # Now deal with STAR fixed STAR fixed ...
    # For an interior `STAR fixed` pairing, we want to do a minimal
    # .*? match followed by `fixed`, with no possibility of backtracking.
    # Atomic groups ("(?>...)") allow us to spell that directly.
    # Note: people rely on the undocumented ability to join multiple
    # translate() results together via "|" to build large regexps matching
    # "one of many" shell patterns.
    while i < n:
        assert inp[i] is STAR
        i += 1
        if i == n:
            add(".*")
            break
        assert inp[i] is not STAR
        pieces: list[str | None] = []  # Pystachy port: for fixed = [], which the join below rebinds to a str (#248)
        while i < n and inp[i] is not STAR:
            pieces.append(inp[i])  # Pystachy port: pieces
            i += 1
        fixed = "".join(pieces)  # Pystachy port: pieces
        if i == n:
            add(".*")
            add(fixed)
        else:
            add(f"(?>.*?{fixed})")
    assert i == n
    joined = "".join(res)  # Pystachy port: for res = "".join(res), rebinding the list to a str (#248)
    return fr'(?s:{joined})\Z'  # Pystachy port: joined
