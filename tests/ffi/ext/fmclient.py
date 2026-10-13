# (tests/ffi/run.sh builds de_DE.UTF-8 in LOCPATH when it can)
import locale
import fm

print(fm.show(1.5))
try:
    locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")
except locale.Error:
    print("no de_DE.UTF-8 locale here")
print(fm.show(1.5))
