/* pyembed.c: CPython in the process of Pystachy code. Linked into every extension module (pystachy
   ext), whose host is CPython (pye_host):
   - Pystachy's sys.stdout and sys.stderr are Python's (std_hook): every write goes through Python's
     sys.stdout or sys.stderr, so the two never interleave out of order, and a replaced sys.stdout
     (contextlib.redirect_stdout) gets Pystachy's prints too.
   - Pystachy's sys.stdin is Python's (in_hook): input() is Python's input(), readline() and read()
     are sys.stdin's, so the two never read ahead of each other.
   - A Python exception becomes a Pystachy one (pye_fail): the first class in its __mro__ that
     Pystachy has, with str(e) (if str(e) raises, what it raised instead); a SystemExit keeps the
     status its code ends the program with, and its args.
   No Python.h: what it uses is CPython's stable ABI, declared below as the ABI fixes it. */
#include <stdint.h>
#include <string.h>
typedef int64_t I;
typedef intptr_t Py_ssize_t;
typedef struct _object PyObject;
typedef struct { I len; uint64_t dict_hash; char s[]; } Str; /* runtime.c's */
/* CPython's stable ABI */
extern PyObject PyUnicode_Type, PyLong_Type;
extern PyObject *PyExc_RuntimeError, *PyExc_TypeError;
int PyGILState_Ensure(void);
void PyGILState_Release(int);
void Py_DecRef(PyObject *);
PyObject *PySys_GetObject(const char *);
PyObject *PyImport_ImportModule(const char *);
PyObject *PyObject_GetAttrString(PyObject *, const char *);
PyObject *PyObject_Vectorcall(PyObject *, PyObject *const *, size_t, PyObject *);
PyObject *PyObject_VectorcallMethod(PyObject *, PyObject *const *, size_t, PyObject *);
PyObject *PyUnicode_FromString(const char *);
PyObject *PyUnicode_DecodeUTF8(const char *, Py_ssize_t, const char *);
const char *PyUnicode_AsUTF8AndSize(PyObject *, Py_ssize_t *);
PyObject *PyUnicode_AsEncodedString(PyObject *, const char *, const char *);
int PyBytes_AsStringAndSize(PyObject *, char **, Py_ssize_t *);
int PyObject_IsInstance(PyObject *, PyObject *);
PyObject *PyLong_FromLongLong(long long);
PyObject *PyErr_Occurred(void);
void PyErr_Clear(void);
void PyErr_SetString(PyObject *, const char *);
PyObject *PyErr_GetRaisedException(void);
PyObject *PyObject_Type(PyObject *);
PyObject *PyObject_Str(PyObject *);
PyObject *PyObject_Repr(PyObject *);
long long PyLong_AsLongLong(PyObject *);
Py_ssize_t PyTuple_Size(PyObject *);
PyObject *PyTuple_GetItem(PyObject *, Py_ssize_t);
#define VC_OFFSET ((size_t)1 << (8 * sizeof(size_t) - 1))   /* PY_VECTORCALL_ARGUMENTS_OFFSET */
/* the runtime (runtime.c) */
typedef struct Exc Exc;
Str *pys_str(const char *p, I n);
_Noreturn void pys_raise(Str *kind, Str *msg);
Exc *pys_exc_new(Str *kind, Str *msg, Str *args);
Exc *pys_exc_exit(I code, Str *str, Str *args);
_Noreturn void pys_throw(Exc *e);
void pys_set_hooks(int (*s)(const char *, I, I), Str *(*i)(I, Str *, I));

static int busy;                       /* in a hook's Python call: an extension module refuses calls then (pye_busy) */
static PyObject *none, *f_input, *s_write, *s_flush, *s_readline, *s_read;

static Str *cstr(const char *s) { return pys_str(s, (I)strlen(s)); }
Str *pye_to_str(PyObject *o) {         /* a Python str as Pystachy's (UTF-8, lone surrogates kept, in the GC heap);
                                          0 with TypeError set if o is no str */
  Py_ssize_t n; char *q;
  if (PyObject_IsInstance(o, &PyUnicode_Type) != 1) {
    if (!PyErr_Occurred()) PyErr_SetString(PyExc_TypeError, "expected str");
    return 0;
  }
  const char *p = PyUnicode_AsUTF8AndSize(o, &n);
  if (p) return pys_str(p, n);
  PyErr_Clear();
  PyObject *b = PyUnicode_AsEncodedString(o, "utf-8", "surrogatepass");
  if (!b) return 0;
  PyBytes_AsStringAndSize(b, &q, &n);
  Str *s = pys_str(q, n); Py_DecRef(b); return s;
}
PyObject *pye_text(Str *s) { return PyUnicode_DecodeUTF8(s->s, s->len, "surrogatepass"); }

/* the builtin classes a Python exception may become */
static const char *const known[] = {"KeyError", "IndexError", "ZeroDivisionError", "OverflowError", "ValueError",
  "TypeError", "AttributeError", "ModuleNotFoundError", "ImportError", "NotImplementedError", "RecursionError",
  "RuntimeError", "FileNotFoundError", "OSError", "StopIteration", "AssertionError", "LookupError",
  "ArithmeticError", "EOFError", "KeyboardInterrupt", "SystemExit", "GeneratorExit", "Exception", "BaseException", 0};
static const char *kind_of(PyObject *e) {   /* the first class in type(e).__mro__ that Pystachy has */
  PyObject *t = PyObject_Type(e), *mro = t ? PyObject_GetAttrString(t, "__mro__") : 0;
  const char *k = 0;
  for (Py_ssize_t i = 0, n = mro ? PyTuple_Size(mro) : 0; i < n && !k; i++) {
    PyObject *nm = PyObject_GetAttrString(PyTuple_GetItem(mro, i), "__name__");   /* (borrowed item) */
    const char *c = nm ? PyUnicode_AsUTF8AndSize(nm, 0) : 0;
    for (int j = 0; c && known[j] && !k; j++) if (!strcmp(c, known[j])) k = known[j];
    Py_DecRef(nm);
  }
  PyErr_Clear(); Py_DecRef(mro); Py_DecRef(t);
  return !k ? "Exception" : !strcmp(k, "RecursionError") ? "RuntimeError" : k;
}
static Exc *exit_of(PyObject *e, Str *ms) {   /* SystemExit e, str(e) ms, as the runtime's: the status its code ends
                                                 the program with (None 0, an int itself, else 1), the args repr(e)
                                                 shows, so that the host gets the same SystemExit back; 0 if repr fails */
  PyObject *c = PyObject_GetAttrString(e, "code"), *r = PyObject_Repr(e);
  Py_ssize_t n = 0;
  const char *p = r ? PyUnicode_AsUTF8AndSize(r, &n) : 0, *a = p ? memchr(p, '(', (size_t)n) : 0;
  Exc *x = 0;
  if (a && p[n - 1] == ')') {
    Str *args = pys_str(a + 1, (I)(p + n - 1 - (a + 1)));
    int isint = c && c != none && PyObject_IsInstance(c, &PyLong_Type) == 1;   /* (a bool too) */
    long long v = isint ? PyLong_AsLongLong(c) : 0;
    if (isint && v == -1 && PyErr_Occurred()) isint = 0;   /* (beyond 64 bits: as a code of another type) */
    x = c == none || isint ? pys_exc_exit(v, ms, args) : pys_exc_new(cstr("SystemExit"), ms, args);
  }
  PyErr_Clear(); Py_DecRef(c); Py_DecRef(r);
  return x;
}
_Noreturn void pye_fail(int g) {       /* the Python exception just raised, raised in Pystachy's code; g: the GIL
                                          state to release first (-1: none) */
  PyObject *e = PyErr_GetRaisedException();
  const char *k = "SystemError";
  Str *ms = 0;
  for (int again = 1; e; again = 0) {
    k = kind_of(e);
    PyObject *m = PyObject_Str(e);
    if (m || !again) { ms = m ? pye_to_str(m) : 0; Py_DecRef(m); break; }
    PyObject *e2 = PyErr_GetRaisedException();   /* str(e) raised: that is raised instead (as the twin's str(e) does) */
    Py_DecRef(e); e = e2;
  }
  Exc *x = e && ms && !strcmp(k, "SystemExit") ? exit_of(e, ms) : 0;
  PyErr_Clear(); Py_DecRef(e);
  Str *kind = cstr(k), *msg = ms ? ms : cstr(e ? "<exception str() failed>" : "error return without exception set");
  if (g >= 0) PyGILState_Release(g);
  if (x) pys_throw(x);
  pys_raise(kind, msg);
}
int pye_busy(void) { return busy; }

static int std_hook(const char *s, I n, I fd) {   /* runtime.c's put1 (n < 0: a flush): 1 when Python took it */
  const char *name = fd == 2 ? "stderr" : "stdout";
  int g = PyGILState_Ensure();
  PyObject *f = PySys_GetObject(name), *r;   /* (borrowed) */
  if (f == none) { PyGILState_Release(g); return 1; }   /* (print() to a None sys.stdout does nothing) */
  if (!f) { PyErr_SetString(PyExc_RuntimeError, fd == 2 ? "lost sys.stderr" : "lost sys.stdout"); pye_fail(g); }
  busy++;
  if (n < 0) r = PyObject_VectorcallMethod(s_flush, &f, 1 | VC_OFFSET, 0);
  else {
    PyObject *u = PyUnicode_DecodeUTF8(s, n, "surrogatepass"), *v[2] = {f, u};
    r = u ? PyObject_VectorcallMethod(s_write, v, 2 | VC_OFFSET, 0) : 0;
    Py_DecRef(u);
  }
  busy--;
  if (!r) pye_fail(g);                 /* (the write raised: a closed file, a broken pipe; print raises it) */
  Py_DecRef(r);
  PyGILState_Release(g);
  return 1;
}
static Str *in_hook(I kind, Str *prompt, I n) {   /* Pystachy's input() (kind 0), sys.stdin.readline() (1), read(n) (2) */
  int g = PyGILState_Ensure();
  PyObject *r = 0;
  busy++;
  if (kind == 0) {                     /* Python's input(): the prompt to sys.stdout, flushed, then sys.stdin's line */
    PyObject *p = prompt ? pye_text(prompt) : 0;
    r = !prompt || p ? PyObject_Vectorcall(f_input, &p, p ? 1 : 0, 0) : 0;
    Py_DecRef(p);
  } else {
    PyObject *f = PySys_GetObject("stdin");   /* (borrowed) */
    if (!f) PyErr_SetString(PyExc_RuntimeError, "lost sys.stdin");
    else if (kind == 1) r = PyObject_VectorcallMethod(s_readline, &f, 1 | VC_OFFSET, 0);
    else {
      PyObject *v[2] = {f, PyLong_FromLongLong(n)};
      r = v[1] ? PyObject_VectorcallMethod(s_read, v, 2 | VC_OFFSET, 0) : 0;
      Py_DecRef(v[1]);
    }
  }
  busy--;
  Str *s = r ? pye_to_str(r) : 0;
  Py_DecRef(r);
  if (!s) pye_fail(g);
  PyGILState_Release(g);
  return s;
}
static int share(void) {               /* what the hooks use of Python; 0 with the error set */
  PyObject *b = PyImport_ImportModule("builtins"), *sys = PyImport_ImportModule("sys");
  if (b && sys && !none) {
    none = PyObject_GetAttrString(b, "None");
    f_input = PyObject_GetAttrString(b, "input");
    s_write = PyUnicode_FromString("write"); s_flush = PyUnicode_FromString("flush");
    s_readline = PyUnicode_FromString("readline"); s_read = PyUnicode_FromString("read");
  }
  Py_DecRef(b); Py_DecRef(sys);
  return none && f_input && s_write && s_flush && s_readline && s_read;
}
int pye_host(void) {                   /* pyext.c: CPython hosts the program (an extension module) */
  if (!share()) return 0;
  pys_set_hooks(std_hook, in_hook);
  return 1;
}

