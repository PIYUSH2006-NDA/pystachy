# error: a tuple's slice bounds must be integer literals (its items' types are known at compile time)
# (a bound known only at run time would leave the slice's item types unknown)
t = (1, "a", 2.5)
n = 1
print(t[n:])
