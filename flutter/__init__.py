import collections.abc
import typing
from typing import cast, Any, Dict, Type, TypeVar, Optional, Union
from typing_extensions import Protocol

CACHED_TYPES: Dict[type, Optional[Dict[str, type]]] = {}


class HasAnnotations(Protocol):
    __annotations__: Dict[str, type]


class Constructable(Protocol):
    def __init__(self, **kwargs: object) -> None: ...


T = TypeVar('T', bound=HasAnnotations)
C = TypeVar('C', bound=Constructable)


def add_indefinite_article(s: str) -> str:
    return ('an ' if s[0].lower() in 'aeiouy' else 'a ') + s


def _get_typename(ty: type) -> str:
    return str(ty).replace('typing.', '')


def english_description_of_type(ty: type, pluralize: bool = False, level: int = 0) -> str:
    plural = 's' if pluralize else ''

    if ty is str:
        return f'string{plural}'

    if ty is int:
        return f'integer{plural}'

    if ty is float:
        return f'number{plural}'

    if ty is bool:
        return f'boolean{plural}'

    if isinstance(ty, type(None)):
        return f'None{plural}'

    level += 1
    if level > 4:
        # Making nested English clauses understandable is hard. Give up.
        return _get_typename(ty)

    origin = getattr(ty, '__origin__', None)
    if origin is not None:
        args = getattr(ty, '__args__')
        if origin is list:
            return f'list{plural} of {english_description_of_type(args[0], True, level)}'
        elif origin is dict:
            key_type = english_description_of_type(args[0], True, level)
            value_type = english_description_of_type(args[1], True, level)
            return f'mapping{plural} of {key_type} to {value_type}'
        elif origin is tuple:
            # Tuples are a hard problem... this is okay
            return _get_typename(ty)
        elif origin is Union:
            if len(args) == 2:
                try:
                    none_index = args.index(type(None))
                except ValueError:
                    pass
                else:
                    non_none_arg = args[int(not none_index)]
                    return f'optional {english_description_of_type(non_none_arg, pluralize, level)}'

            up_to_last = args[:-1]
            part1 = ', '.join(
                add_indefinite_article(english_description_of_type(arg, level=level))
                for arg in up_to_last)
            part2 = add_indefinite_article(english_description_of_type(args[-1], level=level))
            comma = ',' if len(up_to_last) > 1 else ''
            return f'either {part1}{comma} or {part2}'

    try:
        return ty.__name__
    except AttributeError:
        return _get_typename(ty)


def checked(klass: Type[T]) -> Type[T]:
    """Marks a dataclass as being deserializable."""
    CACHED_TYPES[klass] = None
    return klass


class LoadError(TypeError):
    def __init__(self, message: str, ty: type, bad_data: object) -> None:
        super().__init__(message)
        self.expected_type = ty
        self.bad_data = bad_data


class LoadWrongType(LoadError):
    def __init__(self, ty: type, bad_data: object) -> None:
        super().__init__(
            'Incorrect type. Expected {}'.format(english_description_of_type(ty)),
            ty,
            bad_data)


class LoadWrongArity(LoadWrongType):
    pass


class LoadUnknownField(LoadError):
    def __init__(self, ty: type, bad_data: object, bad_field: str) -> None:
        super().__init__('Unexpected field: "{}"'.format(bad_field), ty, bad_data)
        self.bad_field = bad_field


def check_type(ty: Type[C], data: object, ty_module: str = '') -> C:
    # Check for a primitive type
    if ty in (str, int, float, bool, type(None)):
        if not isinstance(data, ty):
            raise LoadWrongType(ty, data)
        return data

    # Check for an object
    if isinstance(data, dict) and ty in CACHED_TYPES:
        annotations = CACHED_TYPES[ty]
        if annotations is None:
            annotations = typing.get_type_hints(ty)
            CACHED_TYPES[ty] = annotations
        result: Dict[str, object] = {}

        # Assign missing fields None
        for key in annotations:
            if key not in data:
                data[key] = None

        # Check field types
        for key, value in data.items():
            if key not in annotations:
                raise LoadUnknownField(ty, data, key)

            expected_type = annotations[key]
            result[key] = check_type(expected_type, value, ty.__module__)

        return ty(**result)

    # Check for one of the special types defined by PEP-484
    origin = getattr(ty, '__origin__', None)
    if origin is not None:
        args = getattr(ty, '__args__')
        if origin is list:
            if not isinstance(data, list):
                raise LoadWrongType(ty, data)
            return cast(C, [check_type(args[0], x, ty_module) for x in data])
        elif origin is dict:
            if not isinstance(data, dict):
                raise LoadWrongType(ty, data)
            key_type, value_type = args
            return cast(C, {
                check_type(key_type, k, ty_module): check_type(value_type, v, ty_module)
                for k, v in data.items()})
        elif origin is tuple and isinstance(data, collections.abc.Collection):
            if not len(data) == len(args):
                raise LoadWrongArity(ty, data)
            return cast(C, tuple(
                check_type(tuple_ty, x, ty_module) for x, tuple_ty in zip(data, args)))
        elif origin is Union:
            for candidate_ty in args:
                try:
                    return cast(C, check_type(candidate_ty, data, ty_module))
                except LoadError:
                    pass

            raise LoadWrongType(ty, data)

        raise LoadError('Unsupported PEP-484 type', ty, data)

    if ty is object or ty is Any:
        return cast(C, data)

    raise LoadError('Unloadable type', ty, data)
