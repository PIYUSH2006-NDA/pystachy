# An imported module's defs whose *args or **kwargs annotation can't be typed are left out, as
# ports/pyfiglet's print_figlet(**kwargs: Any) is: the program uses the module's other defs
import mods.starany
from mods.starany import double

print(double(21), mods.starany.double(1, a=2, b=3))
