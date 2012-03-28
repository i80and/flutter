flutter.py
==========
Python, as a dynamically-typed language, has a philosophy of duck typing: if an
object has the requisite properties, then it is correct.  This usually works
acceptably, but in my experience can on occasion propagate errors through a
system.

While long-term I believe that optional typing can be used to improve static
analysis, for now I'll settle for function prototype assertions at runtime.
This is flutter.py.

Examples
--------
    from flutter import *

    @check(Union(int, float), Function(Union(int, float), int), Tuple(int, str))
    def foo(x, f):
        return (f(x), str(x))
        
    # Works
    foo(3, int)
    
    # Fails
    foo(3, lambda x: str(x))

Documentation
-------------
In general, a value `x` has type `t` if and only if either
`set(dir(x)).issuperset(set(dir(t)))` or if `t` is a type specifier satisfied
by `x`.  In a check() statement, values `0..(n-1)` are arguments, and value
`n` is the return.

  * `flutter.debug` Boolean defaulting to True.  Set to False to disable flutter.check() for performance gains.
  * `flutter.TypeContainer` Abstract base class indicating a type container.
  * `flutter.check(*args)` Function decorator, taking a variable number of types or type specifiers.
  * `flutter.Union(*args)` Value x must be one of the types in args.
  * `flutter.Tuple(*args)` Container x must have the same number and types of elements as args.
  * `flutter.TypedList(arg)` Container x must have only elements of type arg.
  * `flutter.Function(*args)` Value x must be a callable taking arguments of types args[0:-1], returning type args[-1].

TODO
----
  * Tests
  * Better warning messages
  * Support keyword arguments
  * Support function annotations (PEP-3107)
  * Variable assertions
  * Informal static analysis
