# a class template whose field no call can type: an error only where the program makes an object


class Never:
    def __init__(self, v):
        self.v = None


class Fine:
    def __init__(self, v):
        self.v = v
