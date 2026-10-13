import pickle, sys, multiprocessing as mp
import mg
if __name__ == "__main__":
    print("module:", mg.fib.__module__, mg.fib.__name__)
    print(pickle.loads(pickle.dumps(mg.fib))(10))
    sys.stdout.flush()  # (the worker shares this stdout: these lines first)
    p = mp.get_context("spawn").Pool(1)  # (one worker: its import of mg prints once, in a defined order)
    r = p.map(mg.fib, [10, 20, 30])
    p.close()
    p.join()  # (the worker has exited and flushed its output)
    print(r)
