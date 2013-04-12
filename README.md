flutter.py
==========
Python, as a dynamically-typed language, has a philosophy of duck typing: if
an object has the requisite properties, then that object is of the correct
type.  This usually works just fine, but there are some circumstances where
type mistakes can silently propagate throughout a system.

Flutter seeks to detect this early, while it's still easy to debug and before
any corruption can occur.  It provides a modestly expressive type system
capable of wrapping higher-order functions (although those used to ML-style
typesystems may find themselves disappointed).  However, it still remains true
to Python's duck typed style, testing class attribute membership or evaluating
custom verification methods rather than using nominal types.

It's not a static type system, but flutter.py might just make your life easier.

Examples
--------
```python
from flutter import *

# x must be either an int or a float, f must be a function taking either
# an int or a float and returning an int, and a tuple (int, str) must be
# returned.
@check(Union(int, float), Function(Union(int, float), int), Tuple(int, str))
def foo(x, f):
    return (f(x), str(x))

# Works
foo(3, int)

# Throws a TypeError
foo(3, lambda x: str(x))
```

Documentation
-------------
In general, a value `x` has type `t` if and only if either
`set(dir(x)).issuperset(set(dir(t)))` or if `t` is a type specifier satisfied
by `x`.  In a check() statement, values `0..(n-1)` are arguments, and value
`n` is the return.

  * `flutter.debug` Boolean defaulting to True.  Set to False to disable flutter.check() for performance gains.
  * `flutter.check(*args)` Function decorator, taking either a variable number of types or type specifiers, or a list 
  of the same.
  * `flutter.methodcheck(*args)` Like check(), but works with class and instance methods.
  * `flutter.TypeSpecifier` Abstract base class indicating a type specifier.
  * `flutter.Any()` A type specifier that accepts all types.
  * `flutter.Union(*args)` Value x must be one of the types in args.
  * `flutter.Tuple(*args)` Container x must have the same number and types of elements as args.
  * `flutter.TypedIterable(arg)` Container x must have only elements of type arg.
  * `flutter.TypedContainer(container_type, element_type)` Like TypedIterable but with a specific container type.
  * `flutter.Function(*args)` Value x must be a callable taking arguments of types args[0:-1], returning type args[-1].

TODO
----
  * Better warning messages
  * Support keyword arguments
  * Support function annotations (PEP-3107)
  * Variable assertions
  * Informal static type analysis
