#!/usr/bin/env python
import abc

debug = True


class TypeSpecifier(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def validate_type(self, x) -> bool:
        pass

    def wrap_type(self, x):
        return x


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


def create_function_checker(prototype, f):
    def check_function(*args, **kwargs):
        if len(args) != (len(prototype) - 1):
            raise TypeError('{0}() has bad argument arity'.format(f.__name__))

        wrapped_args = []
        for pair in zip(prototype, args):
            if not has_members(pair[1], pair[0]):
                raise TypeError(pair[1])

            if isinstance(pair[0], TypeSpecifier):
                wrapped_args.append(pair[0].wrap_type(pair[1]))
            else:
                wrapped_args.append(pair[1])

        val = f(*wrapped_args, **kwargs)

        if not has_members(val, prototype[-1]):
            raise TypeError(val)

        if isinstance(prototype[-1], TypeSpecifier):
            val = prototype[-1].wrap_type(val)

        return val

    return check_function


class Function(TypeSpecifier):
    def __init__(self, *args):
        self.prototype = args

    def validate_type(self, x):
        if not callable(x):
            return False

        return True

    def wrap_type(self, f):
        wrapper = create_function_checker(self.prototype, f)
        wrapper.__name__ = '{0} (flutter wrapped)'.format(f.__name__)
        return wrapper


def check(*arg_types):
    def inner(f):
        if not debug:
            return f

        return create_function_checker(arg_types, f)
    return inner
