import io, sys
import rd

sys.stdin = io.StringIO("one\ntwo\nthree\nfour\n")
print("host:", input())
print("module:", rd.ask("name? "))
print("module line:", repr(rd.line()))
print("host line:", repr(sys.stdin.readline()))
print("module rest:", repr(rd.rest()))
try:
    rd.ask("")
except EOFError as e:
    print("caught EOFError", e)
old = sys.stdout
sys.stdout = None
rd.shout("not printed")
sys.stdout = old
rd.shout("printed")
