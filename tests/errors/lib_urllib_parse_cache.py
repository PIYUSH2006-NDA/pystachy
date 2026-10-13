# error: 'fn[f:urllib.parse.urlsplit]' has no method 'cache_info'
# (CPython caches urlsplit() with functools.lru_cache, which lib/functools cannot here)
from urllib.parse import urlsplit

urlsplit("http://example.com/")
print(urlsplit.cache_info())
