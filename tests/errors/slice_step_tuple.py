# error: slicing a tuple[int,str] by bounds or a step computed at run time is not supported: the types of the items it selects would not be known
def every(t: tuple[int, str], step: int) -> None:
    print(t[::step])


every((1, "a"), 1)
