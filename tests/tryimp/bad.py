# A module whose code raises, after it binds Y (tests/import_try_binding*.py)
print("bad: init")
Y = 5
raise ValueError("bad raises")
