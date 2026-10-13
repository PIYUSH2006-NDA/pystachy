# error: using **kwargs(name=str, count=int) as a dict is not supported: its values have different types
# lib/string's Template.substitute() with keyword arguments of different types (lib/README.md): it
# looks each placeholder's name up in them as it runs, which a **kwargs record allows only where its
# values share a type
from string import Template

print(Template("$name has $count").substitute(name="Ann", count=3))
