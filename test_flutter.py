from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, List, Dict, Tuple, Type, Optional, Union
from flutter import (
    checked, check_type, english_description_of_type, LoadWrongType,
    LoadWrongArity, LoadError, LoadUnknownField)

Color = Enum('Color', 'red green blue')


@checked
@dataclass
class Base:
    type: str


@checked
@dataclass
class SourceInfo:
    file: str
    line: Tuple[int, int]


@checked
@dataclass
class Node(Base, SourceInfo):
    children: List[Union[str, int, 'Node']]
    options: Optional[Dict[str, str]]
    color: Optional[Color] = field(default=None)
    have_default_factory: str = field(default_factory=str)
    have_default: str = field(default='a')

    # Having a field with a default at the end tests to prevent a quirk in
    # the current implementation of default field values.
    have_default_2: str = field(default='b')


def ensure_failure(func: Callable[[], Any], exception_class: Type[Exception]) -> None:
    exception: Optional[Exception] = None

    try:
        func()
    except exception_class:
        return
    except Exception as err:
        exception = err

    expected_name = exception_class.__name__
    actual_name = exception.__class__.__name__
    raise AssertionError(f'Expected function to raise {expected_name}; got {actual_name}')


def test_ensure_failure() -> None:
    def func() -> None:
        raise ValueError

    ensure_failure(func, ValueError)
    try:
        ensure_failure(func, KeyError)
    except AssertionError:
        pass


def test_successful() -> None:
    result = check_type(Node, {
        'type': 'node',
        'file': 'foo',
        'line': (1, 2),
        'options': {'foo': 'bar'},
        'color': 'green',
        'children': [1, 'foo', {
            'type': 'node',
            'line': (2, 3),
            'file': 'foo',
            'color': 3,
            'children': []}]
    })
    reference_node = Node(type='node', file='foo', line=(1, 2), options={'foo': 'bar'}, children=[
        1,
        'foo',
        Node(type='node', file='foo', line=(2, 3), options=None, color=Color.blue,
             children=[], have_default_factory='', have_default='a', have_default_2='b')],
        have_default_factory='',
        have_default='a',
        have_default_2='b',
        color=Color.green)
    assert result == reference_node


def test_enum_option() -> None:
    assert check_type(Node, {
        'type': 'node',
        'file': 'foo',
        'line': (1, 1),
        'color': None,
        'children': []
    }).color is None


def test_wrong_type() -> None:
    ensure_failure(
        lambda: check_type(Node, {'type': 5, 'file': 'foo', 'line': (1, 2), 'children': []}),
        LoadWrongType)

    ensure_failure(
        lambda: check_type(Node, {'type': 'node', 'file': 'foo', 'line': (1, 2), 'children': 5}),
        LoadWrongType)

    ensure_failure(
        lambda: check_type(Node, {'type': 'node', 'file': 'foo', 'line': 1, 'children': []}),
        LoadWrongType)


def test_wrong_arity() -> None:
    ensure_failure(
        lambda: check_type(Node, {
            'type': 'node', 'file': 'foo', 'line': (1, 2, 3), 'children': []}),
        LoadWrongArity)


def test_no_union_variant() -> None:
    ensure_failure(
        lambda: check_type(Node, {
            'type': 'node', 'file': 'foo', 'line': (1, 2), 'children': [5.5]}),
        LoadWrongType)


def test_bad_recursive_type() -> None:
    ensure_failure(
        lambda: check_type(Node, {'type': 'node', 'file': 'foo', 'line': (1, 2), 'children': [
            Node(type='node', file='foo', line=(2, 3, 4),  # type: ignore
                 options=None, children=[])]}),
        LoadWrongType)


def test_bad_enum() -> None:
    ensure_failure(
        lambda: check_type(Node, {
            'type': 'node', 'file': 'foo', 'line': (1, 2), 'color': {}, 'children': []}),
        LoadWrongType)


def test_too_many_fields() -> None:
    ensure_failure(
        lambda: check_type(Node, {
            'type': 'node', 'file': 'foo', 'line': (1, 2), 'children': [], 'extra': True}),
        LoadUnknownField)


def test_non_dict_into_known_type() -> None:
    """Ensure that loading a non-dict type into a @checked type throws
       LoadWrongType instead of LoadError."""
    ensure_failure(lambda: check_type(Node, []), LoadWrongType)


def test_any_types() -> None:
    @checked
    @dataclass
    class Container:
        obj1: object
        obj2: Any

    assert check_type(Container, {'obj1': 'foo', 'obj2': 'bar'}) == Container('foo', 'bar')
    assert check_type(Container, {'obj1': 5, 'obj2': 10}) == Container(5, 10)


def test_unknown_origin_type() -> None:
    @checked
    @dataclass
    class Container:
        obj1: Callable[[int], int]

    ensure_failure(
        lambda: check_type(Container, {'obj1': 'foo', 'obj2': 'bar'}), LoadError)


def test_type_description() -> None:
    class Bob:
        pass

    ty = List[Union[int, List[Dict[str, Union[int, float]]], object, Bob]]
    desc = ''.join((
        'list of either integers, lists of mappings of strings to Union[int, float]\'s,',
        ' anything, or Bobs'))
    assert english_description_of_type(ty)[0] == desc
    assert english_description_of_type(Union[int, float])[0] == 'either an integer or a number'
    assert english_description_of_type(Union[int])[0] == 'integer'
    assert english_description_of_type(Optional[List[bool]])[0] == 'optional list of booleans'
    assert english_description_of_type(Tuple[int])[0] == 'Tuple[int]'
    assert english_description_of_type(
        Union[int, float, None])[0] == 'either an integer, a number, or nothing'
    assert english_description_of_type(
        Union[int, float, None])[0] == 'either an integer, a number, or nothing'

    # Ensure that unknown PEP-484 types don't throw
    assert english_description_of_type(Callable[[], None])[0] == 'Callable[[], NoneType]'
