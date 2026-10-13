# Where lib/urllib/parse.py differs from CPython's urllib.parse (lib/README.md):
# - where CPython's codecs raise UnicodeEncodeError or UnicodeDecodeError ('strict' errors), the
#   port raises UnicodeError with their message, as Pystachy raises neither: an except clause that
#   names them does not catch it, and the last line, uncaught, prints UnicodeError
# - an encoding other than UTF-8, Latin-1 and ASCII (by any of their names) raises
#   NotImplementedError, where CPython encodes and decodes (or raises LookupError for no codec),
#   and so does the error handler 'namereplace' in quote(), which needs the names of characters
# - a str that holds bytes that are no UTF-8, which no CPython str is, is quoted byte for byte:
#   chr(233) is that byte in Pystachy, and chr(195) + chr(169) the UTF-8 of U+00E9
from urllib.parse import parse_qs, quote, unquote

try:
    print(unquote("%E9", errors="strict"))
except UnicodeDecodeError:
    print("UnicodeDecodeError")
except UnicodeError as e:
    print("UnicodeError:", e)
try:
    print(quote("€", encoding="latin-1"))
except UnicodeEncodeError:
    print("UnicodeEncodeError")
except UnicodeError as e:
    print("UnicodeError:", e)
for enc in ["cp1252", "utf-16", "utf-8-sig", "nosuch"]:
    try:
        print(quote("\xe9", encoding=enc), unquote("%E9", encoding=enc))
    except NotImplementedError as e:
        print("NotImplementedError:", e)
    except LookupError as e:
        print("LookupError:", e)
try:
    print(quote("€", encoding="ascii", errors="namereplace"))
except NotImplementedError as e:
    print("NotImplementedError:", e)
print(quote(chr(233)), quote(chr(195) + chr(169)))
print(parse_qs("q=%E9%41", errors="strict"))
