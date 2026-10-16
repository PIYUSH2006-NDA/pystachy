# codecs.lookup() raises NotImplementedError: Pystachy has no codec registry, where CPython's
# finds the encodings package's codec and returns its CodecInfo (whose attributes are then a
# compile-time error to read: lib/compatibility.md)
import codecs

try:
    codecs.lookup("utf-8")
    print("found")
except NotImplementedError as e:
    print("NotImplementedError:", e)
