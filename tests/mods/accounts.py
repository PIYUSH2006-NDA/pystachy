"""A class deriving from another module's class, whose property it names by an alias."""
from property_setter_mod import Account as Base


class Rounded(Base):
    @Base.balance.setter
    def balance(self, value: int) -> None:
        self._cents = value // 10 * 1000
