# error: cannot infer what recursive() returns: it calls itself before a return statement does; annotate its return type
def recursive():
    return recursive()


print(recursive() + 1)
