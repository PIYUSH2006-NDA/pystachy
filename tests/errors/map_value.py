# error: map_value.py:2: error: map() is supported as the argument of list(), sorted(), sum(), min(), max(), any(), all(), math.fsum(), math.prod(), str.join() and list.extend(), which take its items at once; elsewhere use a list comprehension
squares = map(lambda v: v * v, [1, 2, 3])
print(list(squares))
