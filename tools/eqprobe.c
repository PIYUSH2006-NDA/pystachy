/* A shared DAG must not be expanded into its exponential logical tree by
   equality, ordering or list searches. Count the real runtime's comparisons;
   abort after 64 so an unfixed runtime fails promptly, without a timing limit. */
static void eq_probe(void);
#define EQ_PROBE() eq_probe()
#include "../runtime.c"

I pys_obj_eq(I c, I a, I b) { (void)c; return a == b; }
I pys_obj_cmp(I c, I op, I a, I b) { (void)c; (void)op; return a < b ? -1 : a > b; }
Str *pys_obj_repr(I c, I a, I b) { (void)c; (void)a; (void)b; return cstr("<object>"); }

static I comparisons;
static _Noreturn void bad(const char *what) { fprintf(stderr, "eqprobe: %s\n", what); exit(1); }
static void eq_probe(void) { if (++comparisons > 64) bad("shared DAG traversed more than 64 comparisons"); }
static List *child, *left, *right, *haystack;
static Str *desc;
static void *uleft, *uright, *ualias;
static I *roots[] = {(I *)&child, (I *)&left, (I *)&right, (I *)&haystack, (I *)&desc,
                    (I *)&uleft, (I *)&uright, (I *)&ualias};

int main(void) {
  gc_init(__builtin_frame_address(0), roots, 8);
  child = pys_list_new(1);
  pys_list_append(child, 7);
  for (int i = 0; i < 32; i++) {
    List *parent = pys_list_new(2);
    pys_list_append(parent, (I)child);
    pys_list_append(parent, (I)child);
    child = parent;
  }
  left = pys_list_copy(child);
  right = pys_list_copy(child);
  char d[35]; memset(d, 'L', 33); d[33] = 'i'; d[34] = 0;
  desc = cstr(d);
  if (!pys_eq((I)left, (I)right, desc)) bad("equal DAGs compare unequal");
  if (pys_cmpop((I)left, (I)right, desc, 0) || !pys_cmpop((I)left, (I)right, desc, 1) ||
      pys_cmpop((I)left, (I)right, desc, 2) || !pys_cmpop((I)left, (I)right, desc, 3)) bad("DAG ordering");
  haystack = pys_list_new(2);
  pys_list_append(haystack, (I)left);
  pys_list_append(haystack, (I)left);
  if (pys_list_find(haystack, (I)left, desc) != 0 || pys_list_find(haystack, (I)right, desc) != 0 ||
      pys_list_index(haystack, (I)right, desc, 0, 2) != 0 || pys_list_count(haystack, (I)right, desc) != 2)
    bad("DAG search");
  pys_list_remove(haystack, (I)right, desc);
  if (haystack->len != 1 || haystack->a[0] != (I)left) bad("DAG removal");
  comparisons = 0;
  char ud[64]; snprintf(ud, sizeof(ud), "U2:1:%s2:s", d);
  desc = cstr(ud);
  uleft = pys_ubox(1, (I)left); uright = pys_ubox(1, (I)right); ualias = pys_ubox(1, (I)left);
  if (!pys_eq((I)uleft, (I)uright, desc) || !pys_eq((I)uleft, (I)ualias, desc)) bad("boxed DAG equality");
  haystack = pys_list_new(2);
  pys_list_append(haystack, (I)uleft); pys_list_append(haystack, (I)uleft);
  if (pys_list_find(haystack, (I)ualias, desc) != 0 || pys_list_find(haystack, (I)uright, desc) != 0 ||
      pys_list_index(haystack, (I)uright, desc, 0, 2) != 0 || pys_list_count(haystack, (I)uright, desc) != 2)
    bad("boxed DAG search");
  pys_list_remove(haystack, (I)uright, desc);
  if (haystack->len != 1 || haystack->a[0] != (I)uleft) bad("boxed DAG removal");
  puts("eqprobe: native and union-boxed shared DAG equality and searches passed within 64 comparisons each");
  return 0;
}
