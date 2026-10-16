# error: lib_thread_with.py:5: error: 'with' is supported for files only (with open(...) as f:), not _thread.lock
import _thread

lock = _thread.allocate_lock()
with lock:
    print("held")
