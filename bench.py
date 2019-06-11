import multiprocessing
import pickle
import time
from concurrent.futures import Executor, ProcessPoolExecutor, ThreadPoolExecutor
from interpreterpool import InterpreterPoolExecutor
import nbody

MAX_WORKERS = 4


def bench_serial(fn, *args, **kwargs) -> None:

    t1 = time.time()
    for _ in range(MAX_WORKERS):
        fn(*args, **kwargs)
    t2 = time.time()
    print(f"{'Serial':65s}|{t2 - t1:.6f}|        |        ")


def bench_pickle(fn, *args, **kwargs) -> None:
    """Simulate the round-trip of

    1. pickle input in main process/interpreter
    2. unpickle input in worker
    3. pickle output in worker
    4. unpickle output in main process/interpreter
    """
    t1 = time.time()
    for _ in range(MAX_WORKERS * 2):
        pickle.loads(pickle.dumps((fn, args, kwargs), protocol=pickle.HIGHEST_PROTOCOL))
    t2 = time.time()
    print(f"{'Pickle round-trip':65s}|{t2 - t1:.6f}|        |        ")


def bench_executor(ex: Executor, fn, *args, **kwargs) -> None:
    t1 = time.time()
    with ex:
        futures = [ex.submit(fn, *args, **kwargs) for _ in range(MAX_WORKERS)]
        for future in futures:
            future.result()
        t2 = time.time()

        futures = [ex.submit(fn, *args, **kwargs) for _ in range(MAX_WORKERS)]
        for future in futures:
            future.result()
        t3 = time.time()
    t4 = time.time()

    exargs = [f"max_workers={ex._max_workers}"]
    try:
        exargs.append(f"mp_context={type(ex._mp_context).__name__}")
    except AttributeError:
        pass
    label = f"{type(ex).__name__}({', '.join(exargs)})"
    print(f"{label:65s}|{t3 - t2:.6f}|{t2 - t1:.6f}|{t4 - t3:.6f}")


def bench_all(label, fn, *args, **kwargs) -> None:
    # Github markdown
    print(label)
    print("-" * len(label))
    print(f"{'Method':65s}|{'Warm':8s}|{'Cold':8s}|Teardown")
    print('-' * 65 + '|--------|--------|--------')

    bench_serial(fn, *args, **kwargs)
    bench_pickle(fn, *args, **kwargs)
    for max_workers in (1, MAX_WORKERS):
        bench_executor(ThreadPoolExecutor(max_workers), fn, *args, **kwargs)
        for mp_context in ("spawn", "fork", "forkserver"):
            ex = ProcessPoolExecutor(
                max_workers, mp_context=multiprocessing.get_context(mp_context)
            )
            bench_executor(ex, fn, *args, **kwargs)
        bench_executor(InterpreterPoolExecutor(max_workers), fn, *args, **kwargs)

    print()


def main():
    bench_all("Trivial function", abs, 1)
    bench_all("sleep(0.1) (releases the GIL)", time.sleep, 0.1)
    bodies = nbody.rand_bodies(250)
    bench_all("N-body problem (does not release the GIL)", nbody.nbody, bodies, 0.1)


if __name__ == "__main__":
    main()
