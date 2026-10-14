# urlsplit normalizes an unannotated argument to bool before parsing.
from urllib.parse import urlsplit

print(urlsplit("http://example.com/#f", allow_fragments=0))
print(urlsplit("http://example.com/#f", allow_fragments=1))
