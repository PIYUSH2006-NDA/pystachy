"""Abstract Base Classes (ABCs) according to PEP 3119."""
# abc for Pystachy: CPython imports abc as it starts, so a program's own abc.py is never imported
# there, and Pystachy loads this module for import abc (specs.STANDINS). Its classes are known as
# the program compiles, so the compiler applies what CPython's ABCMeta does at run time: a method
# decorated with abstractmethod in a class that derives from ABC, or whose class statement passes
# metaclass=ABCMeta, is abstract until a subclass defines it again, and making an object of a
# class that has an abstract method raises CPython's TypeError (Gen.abstracts). The docstrings
# are CPython 3.13.16's.


def abstractmethod(funcobj):
    """A decorator indicating abstract methods.

    Requires that the metaclass is ABCMeta or derived from it.  A
    class that has a metaclass derived from ABCMeta cannot be
    instantiated unless all of its abstract methods are overridden.
    The abstract methods can be called using any of the normal
    'super' call mechanisms.  abstractmethod() may be used to declare
    abstract methods for properties and descriptors.

    Usage:

        class C(metaclass=ABCMeta):
            @abstractmethod
            def my_abstract_method(self, arg1, arg2, argN):
                ...
    """
    return funcobj


def abstractclassmethod(callable):
    """A decorator indicating abstract classmethods.

    Deprecated, use 'classmethod' with 'abstractmethod' instead:

        class C(ABC):
            @classmethod
            @abstractmethod
            def my_abstract_classmethod(cls, ...):
                ...

    """
    return callable  # (a method's is @classmethod @abstractmethod, which the compiler applies)


def abstractstaticmethod(callable):
    """A decorator indicating abstract staticmethods.

    Deprecated, use 'staticmethod' with 'abstractmethod' instead:

        class C(ABC):
            @staticmethod
            @abstractmethod
            def my_abstract_staticmethod(...):
                ...

    """
    return callable  # (a method's is @staticmethod @abstractmethod)


def abstractproperty(fget):
    """A decorator indicating abstract properties.

    Deprecated, use 'property' with 'abstractmethod' instead:

        class C(ABC):
            @property
            @abstractmethod
            def my_abstract_property(self):
                ...

    """
    return fget  # (a method's is @property @abstractmethod)


class ABCMeta:
    """Metaclass for defining Abstract Base Classes (ABCs).

    Use this metaclass to create an ABC.  An ABC can be subclassed
    directly, and then acts as a mix-in class.  You can also register
    unrelated concrete classes (even built-in classes) and unrelated
    ABCs as 'virtual subclasses' -- these and their descendants will
    be considered subclasses of the registering ABC by the built-in
    issubclass() function, but the registering ABC won't show up in
    their MRO (Method Resolution Order) nor will method
    implementations defined by the registering ABC be callable (not
    even via super()).
    """
    __slots__ = ()


def get_cache_token() -> int:
    """Returns the current ABC cache token.

The token is an opaque object (supporting equality testing) identifying
the current version of the ABC cache for virtual subclasses.  The token
changes with every call to register() on any ABC."""
    return 0  # (no class is registered: register() is not supported)


class ABC:
    """Helper class that provides a standard way to create an ABC using
    inheritance.
    """
    __slots__ = ()
