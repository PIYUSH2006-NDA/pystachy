"""
Define names for built-in types that aren't directly accessible as a builtin.
"""
# Pystachy's own module, for CPython 3.13's Lib/types.py, of which it has only GenericAlias, for
# CPython's idiom for a generic class: __class_getitem__ = classmethod(GenericAlias) in a class
# body defines nothing in Pystachy, and the class's subscripts are supported in annotations, as
# before, but not at run time. Its other names are CPython's, of what Pystachy does not have
# (functions, methods, code, frames and modules as values, mapping proxies, namespaces, dynamic
# class creation, coroutines): the compiler rejects any use of them, as of GenericAlias elsewhere
from _pystachy_types import (
    AsyncGeneratorType,
    BuiltinFunctionType,
    BuiltinMethodType,
    CapsuleType,
    CellType,
    ClassMethodDescriptorType,
    CodeType,
    CoroutineType,
    DynamicClassAttribute,
    EllipsisType,
    FrameType,
    FunctionType,
    GeneratorType,
    GenericAlias,
    GetSetDescriptorType,
    LambdaType,
    MappingProxyType,
    MemberDescriptorType,
    MethodDescriptorType,
    MethodType,
    MethodWrapperType,
    ModuleType,
    NoneType,
    NotImplementedType,
    SimpleNamespace,
    TracebackType,
    UnionType,
    WrapperDescriptorType,
    _GeneratorWrapper,
    _calculate_meta,
    coroutine,
    get_original_bases,
    new_class,
    prepare_class,
    resolve_bases,
)
