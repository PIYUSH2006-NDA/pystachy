# error: importing module 'warnings' in a function of module 'datetime' is not supported
# The deprecated utcnow() and utcfromtimestamp() warn through the warnings module, which Pystachy
# does not have; datetime.now(timezone.utc) is supported.
from datetime import datetime

print(datetime.utcnow())
