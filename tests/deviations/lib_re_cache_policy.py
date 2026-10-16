# Internal cache policy and retained-entry bounds (CPython has different private cache APIs).
import re

re.purge()
source = "(?P<word>a)"
rx = re.compile(source)
hot = re._compile_template(rx, r"<\g<word>>")
reparsed = 0
for i in range(1025):
    repl = ("." + r"<\g<word>>")[1:]
    if re._compile_template(rx, repl) is not hot:
        reparsed += 1
    re._compile_template(rx, str(i) + r"\g<word>")
    re.compile("cold-" + str(i))
print("hot template reparses", reparsed)
print("pattern bounds", len(re._cache), len(re._cache_front))
print("template bounds", len(re._tcache), len(re._tcache_front))
before = len(re._tcache)
for _ in range(2):
    try:
        re._compile_template(rx, r"\2")
    except re.error:
        print("invalid template uncached", before == len(re._tcache))
re.purge()
print("purge", len(re._cache), len(re._cache_front), len(re._tcache), len(re._tcache_front))
