# Documented deviation: a debug field's text is its expression as written, without comments.
# CPython 3.13 also takes a '#' after a quote inside a triple-quoted string, or inside a nested
# f-string that reuses its quote, for a comment, and drops the text from there (with the '=').
x = "a'#"
print(f"{'''a'#'''=}")
print(f"{f'{'#'}'=}")
print(f"{x=}", f"{'#'=}", f"{x # a comment
=}")
