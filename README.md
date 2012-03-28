flutter.py
==========
Python, as a dynamically-typed language, has a philosophy of duck typing: if an
object has the requisite properties, then it is correct.  This usually works
acceptably, but in my experience can on ocassion propogate errors through a
system.

While long-term I believe that optional typing can be used to improve static
analysis, for now I'll settle for function prototype assertions at runtime.
This is flutter.py.

Examples
========
    from flutter import *

    @check(Union(int, float), Function(Union(int, float), int), Tuple(int, str))
    def foo(x, f):
        return (f(x), str(x))
        
    # Works
    foo(3, int)
    
    # Fails
    foo(3, lambda x: str(x))

TODO
====
  * Tests
  * Better warning messages
  * Support function annotations (PEP-3107)
  * Variable assertions
  * Informal static analysis
