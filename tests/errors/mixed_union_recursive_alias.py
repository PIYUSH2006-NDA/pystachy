# error: mixed_union_recursive_alias.py:6: error: recursive type aliases are not supported: 'Value' refers to itself
from __future__ import annotations

type Value = None | int | float | bool | str | list[Value] | dict[str, Value]

value: Value = {"items": [1, {"nested": True}]}
