#!/bin/sh
# Record what CPython prints for differential tests, the way tests/run.sh runs them:
# tests/NAME.out is stdout followed by "[exit N]"; tests/NAME.err, kept only where CPython
# wrote to stderr, is the last line it wrote there. tests/NAME.in, if present, is stdin; if
# tests/NAME.full exists, stdout is /dev/full (so NAME.out holds only the exit status); if
# tests/NAME.path exists, it is PYTHONPATH (tests/run.sh makes it PYSTACHY_PATH).
# CPython's environment holds PATH and that PYTHONPATH, nothing else of the caller's: FORCE_COLOR
# would color its tracebacks, the caller's PYTHONPATH add modules, PYTHONUNBUFFERED change what
# reaches a stdout the program shares with os.system's commands. Without LANG and LC_*, the locale
# is C, in which CPython runs in UTF-8 mode (PEP 540: PYTHONUTF8=1 changes nothing). It must be the
# CPython of .python-version: another minor version is refused (3.12 prints otherwise for 28
# tests), another patch version warned about.
# tests/record.sh --check records every test into a temporary directory instead, and fails where
# that differs from tests/NAME.out or tests/NAME.err; where CPython prints what a
# tests/deviations/NAME.py must print (its .out: the deviation is gone); where a module of lib/ is
# not the CPython file whose SHA-256 lib/README.md lists; where a .out, .err, .in, .full or .path
# has no tests/NAME.py; and where a *.rej, *.orig or core file lies in the tree.
# usage: tests/record.sh NAME...      (PYTHON=python3.13 tests/record.sh NAME to pick one)
#        tests/record.sh --check
cd "$(dirname "$0")/.." || exit 1
# shellcheck disable=SC3045 # (ulimit -c is not POSIX, but dash, bash, ksh and busybox have it)
ulimit -c 0 2> /dev/null
PY=${PYTHON:-python3}
[ $# != 0 ] || { echo "usage: tests/record.sh NAME... | --check" >&2; exit 2; }
want=$(cat .python-version) || exit 2
have=$(env -i PATH="$PATH" "$PY" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])') || exit 2
case $have in
  "$want") ;;
  "${want%.*}".*) echo "tests/record.sh: warning: $PY is CPython $have, not $want (.python-version)" >&2 ;;
  *) echo "tests/record.sh: $PY is CPython $have, not ${want%.*} (.python-version: $want)" >&2; exit 2 ;;
esac
T=$(mktemp -d "${TMPDIR:-/tmp}/pystachy-record.XXXXXX") || exit 1
trap 'rm -rf "$T"' EXIT
trap 'exit 130' INT TERM
exec 3> /dev/full

# cpython NAME: tests/NAME.py run as tests/run.sh runs it, its stdout and "[exit N]" to $T/NAME.out,
# its stderr to $T/NAME.stderr
cpython() {
  in=/dev/null; [ -f "tests/$1.in" ] && in="tests/$1.in"
  o=1; [ -f "tests/$1.full" ] && o=3
  mp=; [ -f "tests/$1.path" ] && mp=$(cat "tests/$1.path")
  (env -i PATH="$PATH" ${mp:+"PYTHONPATH=$mp"} "$PY" "tests/$1.py" a1 a2 < "$in" >&$o; echo "[exit $?]") > "$T/$1.out" 2> "$T/$1.stderr"
}

if [ "$1" != --check ]; then
  for n; do
    n=$(basename "$n" .py)
    [ -f "tests/$n.py" ] || { echo "tests/record.sh: no tests/$n.py" >&2; exit 2; }
    cpython "$n"
    mv "$T/$n.out" "tests/$n.out"
    if [ -s "$T/$n.stderr" ]; then tail -1 "$T/$n.stderr" > "tests/$n.err"; else rm -f "tests/$n.err"; fi
    echo "$n: $(tail -1 "tests/$n.out") $(cat "tests/$n.err" 2>/dev/null)"
  done
  exit 0
fi
[ $# = 1 ] || { echo "usage: tests/record.sh --check" >&2; exit 2; }

bad=0; nrec=0; ndev=0; nlib=0
for f in tests/*.py; do
  n=$(basename "$f" .py); nrec=$((nrec + 1))
  cpython "$n"
  if ! cmp -s "$T/$n.out" "tests/$n.out"; then
    bad=$((bad + 1)); echo "FAIL $n: tests/$n.out (<) is not what CPython prints (>)"; diff "tests/$n.out" "$T/$n.out" | head -10
  fi
  if [ -s "$T/$n.stderr" ]; then
    tail -1 "$T/$n.stderr" > "$T/$n.err"
    if [ ! -f "tests/$n.err" ]; then
      bad=$((bad + 1)); echo "FAIL $n: CPython writes to stderr, and there is no tests/$n.err: '$(cat "$T/$n.err")'"
    elif ! cmp -s "$T/$n.err" "tests/$n.err"; then
      bad=$((bad + 1)); echo "FAIL $n: CPython's last line of stderr is not tests/$n.err: want '$(cat "tests/$n.err")', CPython '$(cat "$T/$n.err")'"
    fi
  elif [ -f "tests/$n.err" ]; then
    bad=$((bad + 1)); echo "FAIL $n: CPython writes nothing to stderr, but tests/$n.err exists"
  fi
done
# A deviation is gone where CPython prints the hand-written .out: its stdout, the last line of its
# stderr (where Pystachy reports an uncaught exception, after flushing stdout) and its exit status,
# as tests/run.sh runs it
for f in tests/deviations/*.py; do
  n=$(basename "$f" .py); ndev=$((ndev + 1))
  env -i PATH="$PATH" "$PY" "$f" a1 a2 < /dev/null > "$T/dev.out" 2> "$T/dev.err"
  st=$?
  { cat "$T/dev.out"; tail -1 "$T/dev.err"; echo "[exit $st]"; } > "$T/dev.all"
  if cmp -s "$T/dev.all" "tests/deviations/$n.out"; then
    bad=$((bad + 1)); echo "FAIL deviations/$n: CPython prints tests/deviations/$n.out: no deviation left (make it a differential test)"
  fi
done
# lib/README.md's table: | `module` | `Lib/PATH` | `SHA-256` | ... for each unmodified copy lib/PATH
sha() { if command -v sha256sum > /dev/null; then sha256sum "$1"; else shasum -a 256 "$1"; fi 2> /dev/null | cut -c1-64; }
sed -n 's/^| `[^`]*` | `Lib\/\([^`]*\)` | `\([0-9a-f]\{64\}\)` |.*$/\2 lib\/\1/p' lib/README.md > "$T/lib"
while read -r h f; do
  nlib=$((nlib + 1))
  [ "$(sha "$f")" = "$h" ] || { bad=$((bad + 1)); echo "FAIL $f: not the CPython file of lib/README.md (SHA-256 $h)"; }
done < "$T/lib"
[ $nlib != 0 ] || { bad=$((bad + 1)); echo "FAIL lib/README.md: no SHA-256 found in its table"; }
for f in tests/*.out tests/*.err tests/*.in tests/*.full tests/*.path tests/deviations/*.out; do
  [ ! -f "$f" ] || [ -f "${f%.*}.py" ] || { bad=$((bad + 1)); echo "FAIL $f: there is no ${f%.*}.py"; }
done
find . \( -path ./.git -o -path ./build -o -path ./.claude \) -prune -o -type f \
  \( -name '*.rej' -o -name '*.orig' -o -name core -o -name 'core.[0-9]*' \) -print | sed 's|^\./||' > "$T/stray"
while read -r f; do bad=$((bad + 1)); echo "FAIL $f: a stray file (a patch's leftover, a core dump)"; done < "$T/stray"
echo "CPython $have: $nrec recordings, $ndev deviations, $nlib files of lib/ checked; $bad failed"
[ $bad = 0 ]
