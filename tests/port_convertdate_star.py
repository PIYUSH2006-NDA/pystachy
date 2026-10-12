# from convertdate import * (ports/convertdate) takes the names convertdate's __all__ lists: the
# 15 modules the port has. The port leaves out bahai, dublin, french_republican and persian, and
# while __all__ still named them, the import stopped at bahai with an AttributeError.
from convertdate import *

jd = gregorian.to_jd(2024, 3, 11)
print(jd, gregorian.from_jd(jd), julian.from_gregorian(2024, 3, 11), hebrew.from_gregorian(2024, 3, 11))
print(islamic.from_gregorian(2024, 3, 11), coptic.from_gregorian(2024, 3, 11),
      indian_civil.from_gregorian(2024, 3, 11), ordinal.from_gregorian(2024, 3, 11))
print(armenian.from_gregorian(2024, 3, 11), positivist.from_gregorian(2024, 3, 11), utils.jwday(jd))
print(holidays.thanksgiving(2024), holidays.easter(2024))
