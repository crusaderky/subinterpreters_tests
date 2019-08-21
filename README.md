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
[3.8.0b3 binary release](https://www.python.org/downloads/release/python-380b3/)
for MacOSX. It does NOT work on Python shipped by Anaconda as the
``_xxsubinterpreters`` module was (understandably) excluded from compilation.

Notes and known issues
======================
- As of CPython 3.8.0b3, sub-interpreters share the same GIL - which is the
  whole point of the functionality being implemented. See
  [multi-core-python#34](https://github.com/ericsnowcurrently/multi-core-python/issues/34).
- The overhead for creating and destroying sub-interpreters is comparable with 
  creating sub-processes with the ``spawn``
  [start method](https://docs.python.org/3.7/library/multiprocessing.html#contexts-and-start-methods),
  which on *nix is far slower than ``fork`` and ``fork_server``.
- The API of ``_xxsubinterpreters`` as of CPython 3.8.0b3 is different in several points
  from that described in PEP 554. This is likely to further change multiple times in
  the future, and this code might completely break at the next patch to CPython.
- Can't unpickle objects defined in the ``__main__`` module inside a sub-interpreter.
- Can't load modules from the current directory inside a sub-interpreter.
  Workaround:
  ```bash
  export PYTHONPATH=$PWD
  ```
- Missing optimizations for [PEP 574](https://www.python.org/dev/peps/pep-0574/)
  buffers, as the capability to send/receive raw buffers hasn't been implemented yet
  ``_xxsubinterpreters``.

Benchmark results
=================
MacOSX Mojave, Intel Core i7 2.9 GHz, CPython 3.8.0b3 official build:


Trivial function
----------------
Method                                                           |Warm    |Cold    |Teardown
-----------------------------------------------------------------|--------|--------|--------
Serial                                                           |0.000002|        |        
Pickle round-trip                                                |0.000084|        |        
ThreadPoolExecutor(max_workers=1)                                |0.000118|0.000299|0.000056
ProcessPoolExecutor(max_workers=1, mp_context=SpawnContext)      |0.001003|0.067227|0.007244
ProcessPoolExecutor(max_workers=1, mp_context=ForkContext)       |0.001005|0.004655|0.001221
ProcessPoolExecutor(max_workers=1, mp_context=ForkServerContext) |0.000951|0.084088|0.001804
InterpreterPoolExecutor(max_workers=1)                           |0.000553|0.017388|0.004361
ThreadPoolExecutor(max_workers=4)                                |0.000218|0.000363|0.000081
ProcessPoolExecutor(max_workers=4, mp_context=SpawnContext)      |0.001057|0.070887|0.015138
ProcessPoolExecutor(max_workers=4, mp_context=ForkContext)       |0.001027|0.007537|0.002284
ProcessPoolExecutor(max_workers=4, mp_context=ForkServerContext) |0.000989|0.034233|0.002764
InterpreterPoolExecutor(max_workers=4)                           |0.001133|0.068368|0.023322

sleep(0.1) (releases the GIL)
-----------------------------
Method                                                           |Warm    |Cold    |Teardown
-----------------------------------------------------------------|--------|--------|--------
Serial                                                           |0.409683|        |        
Pickle round-trip                                                |0.000152|        |        
ThreadPoolExecutor(max_workers=1)                                |0.411597|0.407856|0.000147
ProcessPoolExecutor(max_workers=1, mp_context=SpawnContext)      |0.410947|0.487474|0.009918
ProcessPoolExecutor(max_workers=1, mp_context=ForkContext)       |0.407302|0.409636|0.002791
ProcessPoolExecutor(max_workers=1, mp_context=ForkServerContext) |0.404946|0.438521|0.002856
InterpreterPoolExecutor(max_workers=1)                           |0.405449|0.435950|0.006723
ThreadPoolExecutor(max_workers=4)                                |0.102878|0.103038|0.000404
ProcessPoolExecutor(max_workers=4, mp_context=SpawnContext)      |0.103998|0.192994|0.014896
ProcessPoolExecutor(max_workers=4, mp_context=ForkContext)       |0.103445|0.110766|0.002816
ProcessPoolExecutor(max_workers=4, mp_context=ForkServerContext) |0.103284|0.142928|0.003820
InterpreterPoolExecutor(max_workers=4)                           |0.104241|0.181633|0.027508

N-body problem (does not release the GIL)
-----------------------------------------
Method                                                           |Warm    |Cold    |Teardown
-----------------------------------------------------------------|--------|--------|--------
Serial                                                           |0.798295|        |        
Pickle round-trip                                                |0.010249|        |        
ThreadPoolExecutor(max_workers=1)                                |0.794965|0.795676|0.000093
ProcessPoolExecutor(max_workers=1, mp_context=SpawnContext)      |0.829979|0.887946|0.007244
ProcessPoolExecutor(max_workers=1, mp_context=ForkContext)       |0.804149|0.811528|0.001768
ProcessPoolExecutor(max_workers=1, mp_context=ForkServerContext) |0.820348|0.844439|0.002542
InterpreterPoolExecutor(max_workers=1)                           |0.824639|0.841333|0.005952
ThreadPoolExecutor(max_workers=4)                                |0.808675|0.813135|0.000193
ProcessPoolExecutor(max_workers=4, mp_context=SpawnContext)      |0.261744|0.326643|0.012183
ProcessPoolExecutor(max_workers=4, mp_context=ForkContext)       |0.269847|0.275312|0.002894
ProcessPoolExecutor(max_workers=4, mp_context=ForkServerContext) |0.273123|0.294871|0.002850
InterpreterPoolExecutor(max_workers=4)                           |0.839553|0.964334|0.040132