#!/bin/sh
# FFI tests (docs/ffi.md). Each runs JIT and AOT, the programs collecting every 7 allocations
# (PYSTACHY_GC_STRESS_PROGRAM):
#   tests/ffi/c_*.py       @ffi.extern (libc, libm, and tests/ffi/ffitest.c built as
#                          libpystachy-ffitest.so on LD_LIBRARY_PATH): stdout and "[exit N]" must be
#                          tests/ffi/NAME.out, which CPython printed with tools/rt_cpython on PYTHONPATH,
#                          and for a run that fails, "[stderr] " and the last line of stderr (the error
#                          raised; --record writes it)
#   tests/ffi/errors/*.py  rejected with the message in the first line
# The compiler checks the IR it builds (PYSTACHY_IRCHECK=1, unless set otherwise). The cases need no
# python; --record runs $PY (default python3) with the twins to write the .out files.
# usage: tests/ffi/run.sh [COMPILER [MODES]]   (default: ./pystachy "jit aot"), or tests/ffi/run.sh --record
cd "$(dirname "$0")/../.." || exit 1
PY=${PY:-python3}
TW=$(pwd)/tools/rt_cpython
T=${TMPDIR:-/tmp}/pystachy-ffi.$$
rm -rf "$T"; mkdir "$T" || exit 1
trap 'rm -rf "$T"' EXIT
trap 'exit 130' INT TERM
# c_lib.py's library
${CC:-cc} -shared -fPIC tests/ffi/ffitest.c -o "$T/libpystachy-ffitest.so" || exit 1
export LD_LIBRARY_PATH="$T${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
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
pass=0; fail=0
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
  n=$(basename "$f" .py); want=$(head -1 "$f" | sed 's/^# error: //')
  if $PYS ir "$f" -o "$T/rej.out" > /dev/null 2> "$T/rej.$n" || ! grep -qF "$want" "$T/rej.$n"; then
    bad "$f: expected error '$want', got: $(cat "$T/rej.$n")"; else ok; fi
done

echo "$pass passed, $fail failed"
[ $fail = 0 ]
