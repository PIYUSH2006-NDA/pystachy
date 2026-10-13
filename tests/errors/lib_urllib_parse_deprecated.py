# error: name 'warnings' is not defined
# (splittype(), the other split functions and to_bytes() are deprecated, and warn with warnings, which Pystachy has not)
from urllib.parse import splittype

print(splittype("http://example.com/"))
