# _thread.start_new_thread() raises NotImplementedError, where CPython starts a thread that calls
# the function: a Pystachy program runs one thread (lib/compatibility.md)
import _thread

done = _thread.allocate_lock()
done.acquire()


def work(n: int) -> None:
    print("work", n)
    done.release()


try:
    _thread.start_new_thread(work, (1,))
    done.acquire()  # (CPython: until the thread has run)
except NotImplementedError as e:
    print("NotImplementedError:", e)
