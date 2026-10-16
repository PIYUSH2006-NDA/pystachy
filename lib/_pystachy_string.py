"""_string's parsers for Pystachy: the format string parsing string.Formatter uses.

Pystachy's subset implementation of CPython 3.13.16's C module _string, whose
formatter_parser() and formatter_field_name_split() (Objects/unicodeobject.c) wrap
MarkupIterator_next(), parse_field(), field_name_split() and FieldNameIterator_next() of
Objects/stringlib/unicode_format.h. They parse as those functions do, with the same
ValueErrors in the same order, but return lists rather than iterators: an error later in a
format string is raised before its first item is used. Strings are indexed by UTF-8 bytes, so
only ASCII digits make a field name an integer, and a conversion specifier is one byte.
"""

__all__ = ["formatter_parser", "formatter_field_name_split"]


def _get_integer(s: str) -> int:
    # get_integer(): the value of s if it is all decimal digits, else -1 (also for "")
    if s == '':
        return -1
    accumulator = 0
    for c in s:
        if c < '0' or c > '9':
            return -1
        digitval = ord(c) - ord('0')
        if accumulator > (9223372036854775807 - digitval) // 10:
            raise ValueError("Too many decimal digits in format string")
        accumulator = accumulator * 10 + digitval
    return accumulator


def formatter_parser(s: str) -> list[tuple[str, str | None, str | None, str | None]]:
    """The (literal_text, field_name, format_spec, conversion) of each part of s.

    literal_text may be empty. field_name, and with it format_spec and conversion, is None
    where no replacement field follows the literal text; format_spec is then a str, and
    conversion None where the field has none.
    """
    out: list[tuple[str, str | None, str | None, str | None]] = []
    start = 0
    end = len(s)
    while start < end:
        # MarkupIterator_next(): the literal text, up to an unescaped brace
        literal_start = start
        c = ''
        markup_follows = False
        while start < end:
            c = s[start]
            start += 1
            if c == '{' or c == '}':
                markup_follows = True
                break
        at_end = start >= end
        length = start - literal_start
        if c == '}' and (at_end or c != s[start]):
            raise ValueError("Single '}' encountered in format string")
        if at_end and c == '{':
            raise ValueError("Single '{' encountered in format string")
        if not at_end:
            if c == s[start]:
                # an escaped { or }: the literal text ends with it, and no field follows
                start += 1
                markup_follows = False
            else:
                length -= 1
        literal = s[literal_start:literal_start + length]
        if not markup_follows:
            out.append((literal, None, None, None))
            continue
        # parse_field(): the field name ends at '}', ':' or '!' (not within [...])
        name_start = start
        c = ''
        while start < end:
            c = s[start]
            start += 1
            if c == '{':
                raise ValueError("unexpected '{' in field name")
            if c == '[':
                while start < end and s[start] != ']':
                    start += 1
                continue
            if c == '}' or c == ':' or c == '!':
                break
        field_name = s[name_start:start - 1]
        format_spec = ''
        conversion: str | None = None
        if c == '!' or c == ':':
            if c == '!':
                if start >= end:
                    raise ValueError("end of string while looking for conversion specifier")
                conversion = s[start] if s[start] != '\0' else None
                start += 1
                if start < end:
                    c = s[start]
                    start += 1
                    if c == '}':
                        out.append((literal, field_name, format_spec, conversion))
                        continue
                    if c != ':':
                        raise ValueError("expected ':' after conversion specifier")
            # the format spec, up to the '}' that closes the field
            spec_start = start
            count = 1
            closed = False
            while start < end:
                c = s[start]
                start += 1
                if c == '{':
                    count += 1
                elif c == '}':
                    count -= 1
                    if count == 0:
                        format_spec = s[spec_start:start - 1]
                        closed = True
                        break
            if not closed:
                raise ValueError("unmatched '{' in format spec")
        elif c != '}':
            raise ValueError("expected '}' before end of string")
        out.append((literal, field_name, format_spec, conversion))
    return out


def formatter_field_name_split(s: str) -> tuple[int | str, list[tuple[bool, int | str]]]:
    """The first part of field name s (an int where it is all digits) and the
    (is_attribute, name or index) of each part after it."""
    # field_name_split(): the first part ends at the first '.' or '['
    i = 0
    end = len(s)
    while i < end:
        c = s[i]
        i += 1
        if c == '[' or c == '.':
            i -= 1
            break
    first = s[:i]
    first_idx = _get_integer(first)
    # FieldNameIterator_next(), for each part after it
    rest: list[tuple[bool, int | str]] = []
    while i < end:
        c = s[i]
        i += 1
        name_start = i
        if c == '.':
            is_attribute = True
            while i < end:
                c = s[i]
                i += 1
                if c == '[' or c == '.':
                    i -= 1
                    break
            name = s[name_start:i]
            name_idx = -1
        elif c == '[':
            is_attribute = False
            bracket_seen = False
            while i < end:
                c = s[i]
                i += 1
                if c == ']':
                    bracket_seen = True
                    break
            if not bracket_seen:
                raise ValueError("Missing ']' in format string")
            name = s[name_start:i - 1]
            name_idx = _get_integer(name)
        else:
            raise ValueError("Only '.' or '[' may follow ']' in format field specifier")
        if name == '':
            raise ValueError("Empty attribute in format string")
        if name_idx != -1:
            rest.append((is_attribute, name_idx))
        else:
            rest.append((is_attribute, name))
    if first_idx != -1:
        return first_idx, rest
    return first, rest
