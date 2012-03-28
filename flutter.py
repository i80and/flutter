#!/usr/bin/env python
import abc

debug = True


class TypeSpecifier(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def validate_type(self, x) -> bool:
        pass


def has_members(a, klass) -> bool:
    """Returns whether or not a contains all of klass's properties."""
    if isinstance(klass, TypeSpecifier):
        return klass.validate_type(a)

    a_props = set(dir(a))
    klass_props = set(dir(klass))
    return a_props.issuperset(klass_props)


class Union(TypeSpecifier):
    def __init__(self, *args):
        self.possible_types = set(args)

    def validate_type(self, x):
        for possible_type in self.possible_types:
            if has_members(x, possible_type):
                return True

        return False


class UnboundedUniform(TypeSpecifier):
    def __init__(self, arg):
        self.type = arg

    def validate_type(self, x):
        for element in x:
            if not has_members(x, self.type):
                return False

        return True


class Tuple(TypeSpecifier):
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


class Function(TypeSpecifier):
    def __init__(self, *args):
        self.function = args

    def validate_type(self, x):
        return True


def check(*arg_types):
    def inner(f):
        if not debug:
            return f

        def checker(*args, **kwargs):
            if len(args) != (len(arg_types) - 1):
                raise TypeError('{0}() has bad argument arity'.format(f.__name__))

            for pair in zip(arg_types, args):
                if not has_members(pair[1], pair[0]):
                    raise TypeError(pair[1])

            val = f(*args, **kwargs)

            if not has_members(val, arg_types[-1]):
                raise TypeError(val)

            return val

        return checker

    return inner
