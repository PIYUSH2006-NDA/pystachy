import property_setter_mod
from property_setter_mod import Account, Savings

a = Account("Zoë", 5)
a.balance += 7
print(a.owner, a.balance)
del a.balance
print(a.balance)
try:
    a.balance = -1
except ValueError as e:
    print("caught", e)
s = property_setter_mod.Savings("Ann", 1)
print(s.balance)
s.balance = 50
print(s.balance)
accounts: list[Account] = [a, s, Savings("Bo", 20)]
for x in accounts:
    x.balance = 3
    print(x.balance)
