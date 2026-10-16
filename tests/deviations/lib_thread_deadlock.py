# Acquiring a locked lock without a timeout raises RuntimeError, where CPython waits for another
# thread to release it, and so does joining a thread handle that is not done: a Pystachy program
# runs one thread (lib/compatibility.md). Under CPython, a thread ends each wait.
import _thread
import time

lock = _thread.allocate_lock()
lock.acquire()
handle = _thread._make_thread_handle(_thread.get_ident() + 1)


def later() -> None:
    time.sleep(0.2)
    lock.release()
    time.sleep(0.2)
    handle._set_done()


try:
    _thread.start_new_thread(later, ())
except NotImplementedError:
    print("no thread")
for k in range(2):
    try:
        if k == 0:
            print(lock.acquire())
        else:
            handle.join()
            print(handle.is_done())
    except RuntimeError as e:
        print("RuntimeError:", e)
