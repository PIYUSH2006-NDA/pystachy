# A submodule whose code raises, after it binds X (tests/import_try_binding*.py)
print("fpk.bad: init")
X = 1
raise ValueError("fpk.bad raises")
