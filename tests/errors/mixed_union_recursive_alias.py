# error: 'type' statements are not supported
from __future__ import annotations

type Value = None | int | float | bool | str | list[Value] | dict[str, Value]

value: Value = {"items": [1, {"nested": True}]}
