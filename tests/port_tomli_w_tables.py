# tomli_w.dumps() of ports/tomli_w on tables: empty documents and tables, nested tables, keys
# that need quotes in table headers, and arrays of tables, which are written inline when each
# table fits on a line of 100 characters (upstream's heuristic) and as [[...]] tables otherwise.
# Many cases are upstream's tests/test_style.py, with values of one type in each container.
import tomli_w

# empty documents and tables (test_empty_doc, test_only_tables, test_dont_write_redundant_tables)
empty: dict[str, str] = {}
print(repr(tomli_w.dumps(empty)))
print(repr(tomli_w.dumps({"a": empty, "b": empty})))
print(repr(tomli_w.dumps({"outer": {"inner": empty}})))
print(repr(tomli_w.dumps({"tab1": {"tab2": {"tab3": empty}}})))

# nested tables, and keys that are quoted in the headers (test_tricky_keys, test_nested_keys)
print(tomli_w.dumps({"server": {"host": "localhost", "port": "8080"}, "client": {"name": "demo"}}))
print(tomli_w.dumps({"a": {"b": {"c": "deep"}}}))
print(tomli_w.dumps({"": {"": {"": 1}}, "a b": {"c.d": {"\u00e9": 2}}, "x": {"y": {"z": 3}}}))

# arrays of tables that stay inline: each table fits in 100 characters (test_array_of_short_tables,
# whose first line is 100 characters long), even where the same table comes twice
print(tomli_w.dumps({"fruit": [{"name": "apple"}, {"name": "banana"}]}))
print(tomli_w.dumps({"table": {"nested-array": [{"a" * 87: 0}, {"b": 1}, {"c": 2}]}}))
row = {"k0": "value number 0", "k1": "value number 1", "k2": "value number 2"}
print(tomli_w.dumps({"rows": [row, row]}))
print(tomli_w.dumps({"points": [{"pos": {"x": 1, "y": 2}}, {"pos": {"x": 3, "y": 4}}]}))
print(tomli_w.dumps({"rows": [empty, empty]}))
print(tomli_w.dumps({"tup": ({"k": "v"}, {"k": "w"})}))
print(tomli_w.dumps({"arrays": [[{"a": "b"}], []]}))

# arrays of tables written as [[...]]: a table of 101 characters, or a line break in one
print(tomli_w.dumps({"table": {"nested-array": [{"a" * 88: 0}, {"b": 1}]}}))
LONG = "x" * 120
print(tomli_w.dumps({"rows": [{"k": LONG}, {"k": "short"}]}))
print(tomli_w.dumps({"tup": ({"k": LONG}, {"k": "w"})}))
print(tomli_w.dumps({"aot": [{"multiline_string": "line1\nline2"}]}, multiline_strings=True))
print(tomli_w.dumps({"aot": [{"multiline_string": "line1\nline2"}]}))

# arrays of tables nested in tables and in arrays of tables (test_array_of_tables_containing_lists,
# test_example_issue_12, test_non_trivial_nesting)
aot = {"aot": [{"a": [0, 1, 2, 3]}]}
print(tomli_w.dumps(aot))
print(tomli_w.dumps({"a": {"nested": aot}}))
print(tomli_w.dumps({"table": {"nested_table": [{"array_options": [1, 2, 3]}, {"another_array": [1, 2]}, {"c": [3]}]}}))
print(tomli_w.dumps({"rows": [{"sub": {"k": LONG}}, {"sub": {"k": "y"}}]}))
print(tomli_w.dumps({"a": [{"b": [{"c": LONG}]}]}))
print(tomli_w.dumps({"top": {"rows": [{"k": LONG}], "more": [{"k": LONG}, {"k": "z"}]}}))
empty_aot: dict[str, dict[str, list[dict[str, str]]]] = {"table": {"array": []}}
print(tomli_w.dumps(empty_aot))
