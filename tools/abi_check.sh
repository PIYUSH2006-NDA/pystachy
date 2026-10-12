#!/bin/sh
# An extension module that `pystachy ext` built must define one dynamic symbol, its entry
# (PyInit_<name> for abi3, PyModExport_<name> for abi3t), and import from CPython only what the
# stable ABI has: every Py* symbol it leaves undefined is a function or data item of
# Misc/stable_abi.toml (a CPython checkout's) added at MAXVER or before, and not one that only some
# builds have (ifdef). Only sh, nm and awk: no python, so it can run in the Python-free stage.
# usage: tools/abi_check.sh STABLE_ABI.TOML MODULE.so MAXVER ENTRY
#        e.g. tools/abi_check.sh Misc/stable_abi.toml fastmath.abi3.so 3.12 PyInit_fastmath
[ $# = 4 ] || { echo "usage: tools/abi_check.sh STABLE_ABI.TOML MODULE.so MAXVER ENTRY" >&2; exit 2; }
toml=$1; so=$2; max=$3; entry=$4
[ -f "$toml" ] || { echo "$toml: no such file" >&2; exit 1; }
[ -f "$so" ] || { echo "$so: no such file" >&2; exit 1; }
defd=$(nm -D --defined-only "$so") && used=$(nm -D --undefined-only "$so") || { echo "$so: nm failed" >&2; exit 1; }
defd=$(echo "$defd" | awk 'NF {print $NF}')
used=$(echo "$used" | awk '$NF ~ /^_?Py/ {print $NF}')
[ "$defd" = "$entry" ] || { echo "$so: defines $(echo "$defd" | tr '\n' ' ')(want only $entry)" >&2; exit 1; }
[ -n "$used" ] || { echo "$so: imports no Py* symbol (not an extension module?)" >&2; exit 1; }
# the stable ABI's functions and data added at MAXVER or before, without an ifdef
ok=$(awk -v max="$max" '
  function num(v, p) { gsub(/[^0-9.]/, "", v); split(v, p, "."); return p[1] * 1000 + p[2] }
  function flush() { if (name != "" && added != "" && !gated && num(added) <= num(max)) print name; name = ""; added = ""; gated = 0 }
  /^\[/ { flush(); if ($0 ~ /^\[(function|data)\./) { name = $0; sub(/^\[[a-z]+\./, "", name); sub(/\].*/, "", name) } next }
  /^[ \t]*added[ \t]*=/ { added = $0; sub(/#.*/, "", added); sub(/^[^=]*=/, "", added) }
  /^[ \t]*ifdef[ \t]*=/ { gated = 1 }
  END { flush() }' "$toml")
bad=$(echo "$used" | while read -r s; do echo "$ok" | grep -qx "$s" || printf '%s ' "$s"; done)
[ -z "$bad" ] || { echo "$so: not in the stable ABI <= $max: $bad" >&2; exit 1; }
echo "${so##*/}: defines only $entry; $(echo "$used" | wc -l) Py symbols, all in the stable ABI <= $max"
