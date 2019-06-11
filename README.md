PEP 554 tools and benchmarks
============================
This is a collection of high-level tools and benchmarks around 
[PEP 554 -- Multiple Interpreters in the Stdlib](https://www.python.org/dev/peps/pep-0554/).

At the moment of writing, it implements:

- ``interpreterpool.py``: ``InterpreterPoolExecutor``, a subclass of
  [concurrent.futures.Executor](https://docs.python.org/3/library/concurrent.futures.html)
- ``bench.py``: Run test problems in all available kinds of Executor
- ``nbody.py``: CPU-intensive algorithm in pure Python which does not release the GIL
  ([N-body problem](https://en.wikipedia.org/wiki/N-body_problem))

Requirements
============
This code has been tested on the CPython 
[3.8.0b1 binary release](https://www.python.org/downloads/release/python-380b1/)
for MacOSX. It does NOT work on Python shipped by Anaconda as the
``_xxsubinterpreters`` module was (understandably) excluded from compilation.

Notes and known issues
======================
- As of CPython 3.8.0b1, sub-interpreters don't release the GIL yet - which is the
  whole point of the functionality.
- The overhead for creating and destroying sub-interpreters is comparable with 
  creating sub-processes with the ``spawn``
  [start method](https://docs.python.org/3.7/library/multiprocessing.html#contexts-and-start-methods),
  which on *nix is far slower than ``fork`` and ``fork_server``.
- The API of ``_xxsubinterpreters`` as of CPython 3.8.0b1 is different in several points
  from that described in PEP 554. This is likely to further change multiple times in
  the future, and this code might completely break at the next patch to CPython.
- Can't unpickle objects defined in the ``__main__`` module inside a sub-interpreter.
  This is likely working as intended.
- Missing optimizations for [PEP 574](https://www.python.org/dev/peps/pep-0574/)
  buffers, as the capability to send/receive raw buffers hasn't been implemented yet
  in CPython 3.8.0b1.

Benchmark results
=================
MacOSX Mojave, Intel Core i7 2.9 GHz, CPython 3.8.0b1 official build:


Trivial function
----------------
Method                                                           |Warm    |Cold    |Teardown
-----------------------------------------------------------------|--------|--------|--------
Serial                                                           |0.000002|        |        
Pickle round-trip                                                |0.000085|        |        
ThreadPoolExecutor(max_workers=1)                                |0.000116|0.000292|0.000047
ProcessPoolExecutor(max_workers=1, mp_context=SpawnContext)      |0.001075|0.069420|0.007123
ProcessPoolExecutor(max_workers=1, mp_context=ForkContext)       |0.001162|0.004759|0.001543
ProcessPoolExecutor(max_workers=1, mp_context=ForkServerContext) |0.001033|0.084911|0.001751
InterpreterPoolExecutor(max_workers=1)                           |0.000484|0.017275|0.004309
ThreadPoolExecutor(max_workers=4)                                |0.000203|0.000312|0.000078
ProcessPoolExecutor(max_workers=4, mp_context=SpawnContext)      |0.001071|0.077575|0.014475
ProcessPoolExecutor(max_workers=4, mp_context=ForkContext)       |0.001321|0.007109|0.001847
ProcessPoolExecutor(max_workers=4, mp_context=ForkServerContext) |0.000976|0.032003|0.002491
InterpreterPoolExecutor(max_workers=4)                           |0.000575|0.069609|0.025059

sleep(0.1) (releases the GIL)
-----------------------------
Method                                                           |Warm    |Cold    |Teardown
-----------------------------------------------------------------|--------|--------|--------
Serial                                                           |0.418047|        |        
Pickle round-trip                                                |0.000151|        |        
ThreadPoolExecutor(max_workers=1)                                |0.415623|0.412865|0.000137
ProcessPoolExecutor(max_workers=1, mp_context=SpawnContext)      |0.412464|0.486085|0.009833
ProcessPoolExecutor(max_workers=1, mp_context=ForkContext)       |0.405673|0.410730|0.002237
ProcessPoolExecutor(max_workers=1, mp_context=ForkServerContext) |0.404769|0.439465|0.002643
InterpreterPoolExecutor(max_workers=1)                           |0.416656|0.436714|0.006724
ThreadPoolExecutor(max_workers=4)                                |0.104060|0.104992|0.000194
ProcessPoolExecutor(max_workers=4, mp_context=SpawnContext)      |0.102422|0.187271|0.014333
ProcessPoolExecutor(max_workers=4, mp_context=ForkContext)       |0.101842|0.109868|0.002505
ProcessPoolExecutor(max_workers=4, mp_context=ForkServerContext) |0.103284|0.139800|0.003499
InterpreterPoolExecutor(max_workers=4)                           |0.105254|0.179008|0.028538

N-body problem (does not release the GIL)
-----------------------------------------
Method                                                           |Warm    |Cold    |Teardown
-----------------------------------------------------------------|--------|--------|--------
Serial                                                           |0.834375|        |        
Pickle round-trip                                                |0.010707|        |        
ThreadPoolExecutor(max_workers=1)                                |0.794126|0.796729|0.000084
ProcessPoolExecutor(max_workers=1, mp_context=SpawnContext)      |0.795121|0.856521|0.006806
ProcessPoolExecutor(max_workers=1, mp_context=ForkContext)       |0.812442|0.810960|0.002012
ProcessPoolExecutor(max_workers=1, mp_context=ForkServerContext) |0.793814|0.821177|0.001973
InterpreterPoolExecutor(max_workers=1)                           |0.804765|0.827425|0.006350
ThreadPoolExecutor(max_workers=4)                                |0.808185|0.809991|0.000389
ProcessPoolExecutor(max_workers=4, mp_context=SpawnContext)      |0.246158|0.314358|0.012593
ProcessPoolExecutor(max_workers=4, mp_context=ForkContext)       |0.254898|0.261133|0.002364
ProcessPoolExecutor(max_workers=4, mp_context=ForkServerContext) |0.249963|0.278060|0.002725
InterpreterPoolExecutor(max_workers=4)                           |0.824350|0.951046|0.043593