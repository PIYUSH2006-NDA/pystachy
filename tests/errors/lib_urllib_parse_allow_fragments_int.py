# error: expected int, got bool
# (urlsplit() rebinds allow_fragments to bool(allow_fragments), and a variable has one type)
from urllib.parse import urlsplit

print(urlsplit("http://example.com/#f", allow_fragments=0))
