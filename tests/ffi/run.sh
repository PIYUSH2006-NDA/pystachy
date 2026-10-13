#!/bin/sh
# FFI tests (docs/ffi.md). Each runs JIT and AOT, the programs collecting every 7 allocations
# (PYSTACHY_GC_STRESS_PROGRAM; every allocation for an extension module):
#   tests/ffi/c_*.py       @ffi.extern (libc, libm, and tests/ffi/ffitest.c built as
#                          libpystachy-ffitest.so on LD_LIBRARY_PATH): stdout and "[exit N]" must be
#                          tests/ffi/NAME.out, which CPython printed with tools/rt_cpython on PYTHONPATH,
#                          and for a run that fails, "[stderr] " and the last line of stderr (the error
#                          raised; --record writes it)
#   tests/ffi/errors/*.py  rejected with the message in the first line ("pystachy ext" for ext_*.py)
#   tests/ffi/ext/*.py     pystachy ext: the modules that import export from ffi become extension
#                          modules (abi3; abi3t on a free-threaded CPython), and each client prints with
#                          them what it prints with their source and tools/rt_cpython (its 'loaded' and
#                          'gil' lines aside: they name the file, and the GIL an extension turns on)
# The compiler checks the IR it builds (PYSTACHY_IRCHECK=1, unless set otherwise).
# The c_ and error cases need no python: without $PY (default python3, 3.12 or later, with a shared
# libpython) the ext cases are skipped, and the report says so.
# usage: tests/ffi/run.sh [COMPILER [MODES]]   (default: ./pystachy "jit aot"), or tests/ffi/run.sh --record
cd "$(dirname "$0")/../.." || exit 1
PY=${PY:-python3}
TW=$(pwd)/tools/rt_cpython
T=${TMPDIR:-/tmp}/pystachy-ffi.$$
rm -rf "$T"; mkdir "$T" || exit 1
trap 'rm -rf "$T"' EXIT
trap 'exit 130' INT TERM
# c_lib.py's library; and a de_DE.UTF-8 locale (a comma for the decimal point) for ext/fmclient.py,
# if localedef can build one (else it prints that there is none, both runs alike)
${CC:-cc} -shared -fPIC tests/ffi/ffitest.c -o "$T/libpystachy-ffitest.so" || exit 1
export LD_LIBRARY_PATH="$T${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
mkdir -p "$T/locales"
localedef -i de_DE -f UTF-8 "$T/locales/de_DE.UTF-8" > /dev/null 2>&1
export LOCPATH="$T/locales"
# stderr's last line after "[exit N]" of a run that failed: cerr OUT ERR
cerr() { if [ "$(tail -1 "$1")" != "[exit 0]" ]; then echo "[stderr] $(tail -1 "$2")" >> "$1"; fi; }
if [ "$1" = --record ]; then
  for f in tests/ffi/c_*.py; do
    (PYTHONPATH=$TW env -u PYTHONUNBUFFERED "$PY" "$f" a1 a2 < /dev/null; echo "[exit $?]") > "${f%.py}.out" 2> "$T/rec.err"
    cerr "${f%.py}.out" "$T/rec.err"
    echo "${f%.py}.out: $(tail -1 "${f%.py}.out")"
  done
  exit 0
fi
PYS=${1:-./pystachy}
MODES=${2:-jit aot}
export PYSTACHY_IRCHECK="${PYSTACHY_IRCHECK:-1}"  # (the compiler checks the IR it builds, as in tests/run.sh)
pass=0; fail=0; skipped=
ok() { pass=$((pass + 1)); }
bad() { fail=$((fail + 1)); echo "FAIL $*"; }

# @ffi.extern
for f in tests/ffi/c_*.py; do
  n=$(basename "$f" .py)
  for mode in $MODES; do
    if [ "$mode" = jit ]; then
      (PYSTACHY_GC_STRESS_PROGRAM=7 $PYS run "$f" a1 a2 < /dev/null; echo "[exit $?]") > "$T/$n.$mode" 2> "$T/$n.err"
    else
      $PYS build "$f" -o "$T/$n.exe" 2> "$T/$n.err" && (PYSTACHY_GC_STRESS=7 "$T/$n.exe" a1 a2 < /dev/null; echo "[exit $?]") > "$T/$n.$mode" 2>> "$T/$n.err"
    fi
    cerr "$T/$n.$mode" "$T/$n.err"
    if cmp -s "$T/$n.$mode" "tests/ffi/$n.out"; then ok; else bad "$n ($mode)"; diff "tests/ffi/$n.out" "$T/$n.$mode" | head -10; head -5 "$T/$n.err"; fi
  done
done
for f in tests/ffi/errors/*.py; do
  n=$(basename "$f" .py); want=$(head -1 "$f" | sed 's/^# error: //'); how=ir
  case $n in ext_*) how=ext ;; esac
  if $PYS $how "$f" -o "$T/rej.out" > /dev/null 2> "$T/rej.$n" || ! grep -qF "$want" "$T/rej.$n"; then
    bad "$f: expected error '$want', got: $(cat "$T/rej.$n")"; else ok; fi
done

# CPython: $PY 3.12 or later, and its shared libpython (in LIBDIR, or a relocated build's lib/)
info=$("$PY" -c 'import os, sys, sysconfig as s
d, l = s.get_config_var("LIBDIR") or "", s.get_config_var("INSTSONAME") or ""
p = [x for x in (os.path.join(d, l), os.path.join(sys.base_prefix, "lib", l)) if ".so" in l and os.path.exists(x)]
print(p[0] if sys.version_info >= (3, 12) and p else "-",
      "t" if s.get_config_var("Py_GIL_DISABLED") else "-", sys.version_info[1])' 2> /dev/null)
# shellcheck disable=SC2086
set -- ${info:--}
LIBPY=${1#-}; FT=${2#-}; MINOR=$3
if [ -z "$LIBPY" ]; then
  skipped="the ext cases (no $PY 3.12+ with a shared libpython)"
else
  # pystachy ext: abi3 (3.12+ GIL builds) or abi3t (3.15+, needed by free-threaded ones)
  abi=abi3; [ -n "$FT" ] && abi=abi3t
  if [ -n "$FT" ] && [ "$MINOR" -lt 15 ]; then
    skipped="the ext cases (a free-threaded CPython before 3.15 loads no extension module of Pystachy's)"
  else
    mkdir -p "$T/src" "$T/so"
    cp tests/ffi/ext/*.py "$T/src/"; cp tests/ffi/ext/*.py "$T/so/"
    for f in tests/ffi/ext/*.py; do
      n=$(basename "$f" .py)
      grep -q '^from ffi import export' "$f" || continue
      rm -f "$T/so/$n.py"
      if $PYS ext "$f" --abi $abi -o "$T/so/$n.$abi.so" 2> "$T/ext.$n.err"; then ok; else bad "pystachy ext $f"; head -5 "$T/ext.$n.err"; fi
    done
    for c in client.py client2.py avclient.py pk3.py rdclient.py fmclient.py; do
      st=1
      for d in src so; do
        tw=; [ $d = src ] && tw=$TW
        (cd "$T/$d" && PYTHONPATH=$tw PYSTACHY_GC_STRESS=$st "$PY" -W ignore "$c" a b < /dev/null > "$T/$c.$d" 2>&1; echo "[exit $?]" >> "$T/$c.$d")
        grep -v -e '^loaded ' -e '^gil ' "$T/$c.$d" > "$T/$c.$d.cmp"
      done
      if cmp -s "$T/$c.src.cmp" "$T/$c.so.cmp"; then ok; else bad "ext client $c (CPython 3.$MINOR$FT, $abi)"; diff "$T/$c.src.cmp" "$T/$c.so.cmp" | head -10; fi
    done
  fi
fi
echo "$pass passed, $fail failed${skipped:+; skipped: $skipped}"
[ $fail = 0 ]
