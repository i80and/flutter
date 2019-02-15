import collections.abc
import dataclasses
import enum
import typing
from dataclasses import MISSING
from typing import cast, Any, Callable, Dict, Set, Tuple, Type, TypeVar, Iterator, Optional, Union
from typing_extensions import Protocol


@dataclasses.dataclass
class _Field:
    """A single field in a _TypeThunk."""
    __slots__ = ('default_factory', 'type')

    default_factory: Optional[Callable[[], Any]]
    type: Type[Any]


class _TypeThunk:
    """Type hints cannot be fully resolved at module runtime due to ForwardRefs. Instead,
       store the type here, and resolve type hints only when needed. By that time, hopefully all
       types have been declared."""
    __slots__ = ('type', '_fields')

    def __init__(self, klass: Type[Any]) -> None:
        self.type = klass
        self._fields: Optional[Dict[str, _Field]] = None

    def __getitem__(self, field_name: str) -> _Field:
        return self.fields[field_name]

    def __iter__(self) -> Iterator[str]:
        return iter(self.fields.keys())

    @property
    def fields(self) -> Dict[str, _Field]:
        def make_factory(value: object) -> Callable[[], Any]:
            return lambda: value

        if self._fields is None:
            hints = typing.get_type_hints(self.type)
            # This is gnarly. Sorry. For each field, store its default_factory if present; otherwise
            # create a factory returning its default if present; otherwise None. Default parameter
            # in the lambda is a ~~hack~~ to avoid messing up the variable binding.
            fields: Dict[str, _Field] = {
                field.name: _Field(
                    field.default_factory if field.default_factory is not MISSING  # type: ignore
                    else ((make_factory(field.default)) if field.default is not MISSING
                          else None),
                    hints[field.name]) for field in dataclasses.fields(self.type)
            }

            self._fields = fields

        return self._fields


CACHED_TYPES: Dict[type, _TypeThunk] = {}


class HasAnnotations(Protocol):
    __annotations__: Dict[str, type]


class Constructable(Protocol):
    def __init__(self, **kwargs: object) -> None: ...


T = TypeVar('T', bound=HasAnnotations)
C = TypeVar('C', bound=Constructable)


def _add_indefinite_article(s: str) -> str:
    if s == 'nothing':
        return s

    return ('an ' if s[0].lower() in 'aeiouy' else 'a ') + s


def _get_typename(ty: type) -> str:
    return str(ty).replace('typing.', '')


def _pluralize(s: str) -> str:
    if s[-1].isalpha():
        return s + 's'

    return s + '\'s'


def _generate_hint(ty: type, get_description: Callable[[type], str]) -> str:
    try:
        name = ty.__name__
    except AttributeError:
        return str(ty)
    docstring = '\n'.join('  ' + line for line in (ty.__doc__ or '').split('\n'))
    fields = '\n'.join(f'  {k}: {get_description(v)}'
                       for k, v in typing.get_type_hints(ty).items() if not k.startswith('_'))
    return f'{name}:\n{docstring}\n{fields}'


def english_description_of_type(ty: type) -> Tuple[str, Dict[type, str]]:
    hints: Dict[type, str] = {}

    def inner(ty: type, plural: bool, level: int) -> str:
        pluralize = _pluralize if plural else lambda s: s
        plural_suffix = 's' if plural else ''

        if ty is str:
            return pluralize('string')

        if ty is int:
            return pluralize('integer')

        if ty is float:
            return pluralize('number')

        if ty is bool:
            return pluralize('boolean')

        if ty is type(None):  # noqa
            return 'nothing'

        if ty is object or ty is Any:
            return 'anything'

        level += 1
        if level > 4:
            # Making nested English clauses understandable is hard. Give up.
            return pluralize(_get_typename(ty))

        origin = getattr(ty, '__origin__', None)
        if origin is not None:
            args = getattr(ty, '__args__')
            if origin is list:
                return f'list{plural_suffix} of {inner(args[0], True, level)}'
            elif origin is dict:
                key_type = inner(args[0], True, level)
                value_type = inner(args[1], True, level)
                return f'mapping{plural_suffix} of {key_type} to {value_type}'
            elif origin is tuple:
                # Tuples are a hard problem... this is okay
                return pluralize(_get_typename(ty))
            elif origin is Union:
                if len(args) == 2:
                    try:
                        none_index = args.index(type(None))
                    except ValueError:
                        pass
                    else:
                        non_none_arg = args[int(not none_index)]
                        return f'optional {inner(non_none_arg, plural, level)}'

                up_to_last = args[:-1]
                part1 = (inner(arg, plural, level=level) for arg in up_to_last)
                part2 = inner(args[-1], plural, level=level)
                if not plural:
                    part1 = (_add_indefinite_article(desc) for desc in part1)
                    part2 = _add_indefinite_article(part2)
                comma = ',' if len(up_to_last) > 1 else ''
                joined_part1 = ', '.join(part1)
                return f'either {joined_part1}{comma} or {part2}'

        # A custom type
        if ty not in hints:
            hints[ty] = _generate_hint(ty, lambda ty: inner(ty, False, level))

        try:
            return pluralize(ty.__name__)
        except AttributeError:
            return pluralize(_get_typename(ty))

    return inner(ty, False, 0), hints


def checked(klass: Type[T]) -> Type[T]:
    """Marks a dataclass as being deserializable."""
    CACHED_TYPES[klass] = _TypeThunk(klass)
    return klass


class LoadError(TypeError):
    def __init__(self, message: str, ty: type, bad_data: object) -> None:
        super().__init__(message)
        self.expected_type = ty
        self.bad_data = bad_data


class LoadWrongType(LoadError):
    def __init__(self, ty: type, bad_data: object) -> None:
        description, hints = english_description_of_type(ty)
        hint_text = '\n\n'.join(hints.values())
        if hint_text:
            hint_text = '\n\n' + hint_text

        super().__init__(
            f'Incorrect type. Expected {description}.{hint_text}',
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
    if isinstance(ty, type) and issubclass(ty, (str, int, float, bool, type(None))):
        if not isinstance(data, ty):
            raise LoadWrongType(ty, data)
        return cast(C, data)

    if isinstance(ty, enum.EnumMeta):
        if isinstance(data, str):
            return ty[data]
        if isinstance(data, int):
            return ty(data)

    # Check for an object
    if isinstance(data, dict) and ty in CACHED_TYPES:
        annotations = CACHED_TYPES[ty]
        result: Dict[str, object] = {}

        # Assign missing fields None
        missing: Set[str] = set()
        for key in annotations:
            if key not in data:
                data[key] = None
                missing.add(key)

        # Check field types
        for key, value in data.items():
            if key not in annotations:
                raise LoadUnknownField(ty, data, key)

            field = annotations[key]
            have_value = False
            if key in missing:
                # Use the field's default_factory if it's defined
                if field.default_factory is not None:
                    result[key] = field.default_factory()
                    have_value = True

            if not have_value:
                result[key] = check_type(field.type, value, ty.__module__)

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
