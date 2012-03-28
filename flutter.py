#!/usr/bin/env python
import abc

debug = True


class TypeContainer(metaclass=abc.ABCMeta):
    """Base-class for special type containers."""
    @abc.abstractmethod
    def validate_type(self, x) -> bool:
        """Verify that x satisfies this type specifier."""
        pass

    def wrap_type(self, x):
        """Some types (like functions) cannot have their type resolved just
           yet, and must be safety-wrapped for later analysis."""
        return x


def has_members(a, klass) -> bool:
    """Returns whether or not a contains all of klass's properties."""
    # Type containers have special validators
    if isinstance(klass, TypeContainer):
        return klass.validate_type(a)

    a_props = set(dir(a))
    klass_props = set(dir(klass))
    return a_props.issuperset(klass_props)


class Union(TypeContainer):
    """Type container requiring that a value be one among a set of types."""
    def __init__(self, *args):
        self.possible_types = set(args)

    def validate_type(self, x):
        for possible_type in self.possible_types:
            if has_members(x, possible_type):
                return True

        return False


class TypedList(TypeContainer):
    """Type container requiring that each element in a value be of a certain
       type."""
    def __init__(self, arg):
        self.type = arg

    def validate_type(self, x):
        for element in x:
            if not has_members(x, self.type):
                return False

        return True


class Tuple(TypeContainer):
    """Type container requiring that a value have N elements, each of a
       predetermined type."""
    def __init__(self, *args):
        self.length = len(args)
        self.types = args

    def validate_type(self, x):
        if len(x) != self.length:
            return False

        for pair in zip(x, self.types):
            if not has_members(pair[0], pair[1]):
                return False

        return True


def create_function_checker(prototype, f):
    """Returns a wrapper for f demanding that f fits the given prototype."""
    def check_function(*args, **kwargs):
        """If the arguments are right, call f() with them, and check its
           return value."""
        # Check the argument array arity
        if len(args) != (len(prototype) - 1):
            raise TypeError('{0}() has bad argument arity'.format(f.__name__))

        # Ensure that the argument array is correct, wrapping functions as
        # necessary before passing them on to f()
        wrapped_args = []
        for pair in zip(prototype, args):
            if not has_members(pair[1], pair[0]):
                raise TypeError(pair[1])

            if isinstance(pair[0], TypeContainer):
                wrapped_args.append(pair[0].wrap_type(pair[1]))
            else:
                wrapped_args.append(pair[1])

        # Check f()'s return value, and wrap it if necessary before returning
        val = f(*wrapped_args, **kwargs)
        if not has_members(val, prototype[-1]):
            raise TypeError(val)
        if isinstance(prototype[-1], TypeContainer):
            val = prototype[-1].wrap_type(val)

        return val

    return check_function


class Function(TypeContainer):
    """A type container representing a function."""
    def __init__(self, *args):
        self.prototype = args

    def validate_type(self, x):
        if not callable(x):
            return False

        return True

    def wrap_type(self, f):
        """Functions cannot have their type determined upon instantiation."""
        wrapper = create_function_checker(self.prototype, f)
        wrapper.__name__ = '{0} (flutter wrapped)'.format(f.__name__)
        return wrapper


def check(*arg_types):
    """Simple function decorator that checks the given function."""
    def inner(f):
        if not debug:
            return f

        return create_function_checker(arg_types, f)
    return inner
