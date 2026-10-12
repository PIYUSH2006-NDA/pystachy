class Among:
    # Pystachy port: annotated, and no method= (a function as a value); only finnish,
    # hindi and polish pass one
    def __init__(self, s: str, substring_i: int, result: int):
        """
        @ivar s search string
        @ivar substring index to longest matching substring
        @ivar result of the lookup
        @ivar method method to use if substring matches
        """
        self.s = s
        self.substring_i = substring_i
        self.result = result
        # Pystachy port: no self.method (see above)
