import _xxsubinterpreters as interpreters
import multiprocessing
import pickle
import threading
from warnings import warn
from textwrap import dedent
from typing import Any, Callable, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, Future


class InterpreterPoolExecutor(ThreadPoolExecutor):
    """An :class:`~concurrent.futures.Executor` subclass that executes calls
    asynchronously using a pool of at most *max_workers* interpreters. If *max_workers*
    is None or not given, it will default to the number of processors on the machine. If
    *max_workers* is lower or equal to 0, then a :class:`ValueError` will be raised.

    *thread_name_prefix* is an optional argument to allow users to control the
    :class:`threading.Thread` names for minder threads created by the pool for easier
    debugging.

    *initializer* is an optional callable that is called at the start of each worker
    interpreter; *initargs* is a tuple of arguments passed to the initializer. Should
    *initializer* raise an exception, all currently pending jobs will raise a
    :class:`~concurrent.futures.BrokenProcessPool`, as well any attempt to submit more
    jobs to the pool.
    """

    interpreters: Dict[int, Tuple[interpreters.InterpreterID, interpreters.ChannelID]]

    def __init__(
        self,
        max_workers: int = None,
        thread_name_prefix: str = "",
        initializer: Callable[..., None] = None,
        initargs: tuple = (),
    ):
        self.interpreters = {}

        if max_workers is None:
            max_workers = multiprocessing.cpu_count()

        super().__init__(
            max_workers=max_workers,
            thread_name_prefix=thread_name_prefix,
            initializer=self._initializer,
            initargs=(initializer,) + initargs,
        )

    def _initializer(
        self, user_initializer: Callable[..., None] = None, *initargs: Any
    ) -> None:
        """Create a sub-interpreter and optionally run user-defined
        initializer function inside it
        """
        thread_id = threading.get_ident()
        interp_id = interpreters.create()
        chan_id = interpreters.channel_create()
        self.interpreters[thread_id] = interp_id, chan_id
        if user_initializer:
            init_bytes = pickle.dumps(
                (user_initializer, initargs), protocol=pickle.HIGHEST_PROTOCOL
            )
            interpreters.run_string(
                interp_id,
                dedent(
                    """
                    import pickle
                    import _xxsubinterpreters as interpreters
        
                    initializer, initargs = pickle.loads(init_bytes)
                    initializer(*initargs)
                    """
                ),
                shared={"init_bytes": init_bytes},
            )
        else:
            interpreters.run_string(
                interp_id,
                dedent(
                    """
                    import pickle
                    import _xxsubinterpreters as interpreters
                    """
                ),
                shared={},
            )

    def submit(self, fn: Callable, *args, **kwargs) -> Future:
        return super().submit(self._run, fn, *args, **kwargs)

    def _run(self, fn: Callable, *args, **kwargs):
        thread_id = threading.get_ident()
        interp_id, chan_id = self.interpreters[thread_id]
        fn_bytes = pickle.dumps((fn, args, kwargs), protocol=pickle.HIGHEST_PROTOCOL)

        interpreters.run_string(
            interp_id,
            dedent(
                """
                fn, args, kwargs = pickle.loads(fn_bytes)
                retval_obj = fn(*args, **kwargs)
                retval_bytes = pickle.dumps(
                    retval_obj,
                    protocol=pickle.HIGHEST_PROTOCOL
                )
                interpreters.channel_send(chan_id, retval_bytes)
                """
            ),
            shared={"fn_bytes": fn_bytes, "chan_id": chan_id},
        )

        retval_bytes = interpreters.channel_recv(chan_id)
        return pickle.loads(retval_bytes)

    def shutdown(self, wait: bool = True) -> None:
        super().shutdown(wait=wait)
        for interp_id, chan_id in self.interpreters.values():
            interpreters.channel_destroy(chan_id)
            if not interpreters.is_running(interp_id):
                interpreters.destroy(interp_id)
            else:
                assert not wait
                warn("Leaving orphaned interpreter %s" % interp_id)
