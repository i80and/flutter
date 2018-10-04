#!/usr/bin/env python3

from dataclasses import dataclass
from typing import Any, Callable, List, Dict, Tuple, Type, Optional, Union
from flutter import (
    checked, check_type, LoadWrongType, LoadWrongArity, LoadError,
    LoadUnknownField)


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


def ensure_failure(func: Callable, exception_class: Type[Exception]) -> None:
    try:
        func()
    except exception_class:
        return
    except Exception:
        pass

    raise AssertionError('Expected function to raise {}'.format(exception_class.__name__))


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
        'children': [1, 'foo', {'type': 'node', 'line': (2, 3), 'file': 'foo', 'children': []}]
    })
    reference_node = Node(type='node', file='foo', line=(1, 2), options={'foo': 'bar'}, children=[
        1, 'foo', Node(type='node', file='foo', line=(2, 3), options=None, children=[])])
    assert result == reference_node


def test_wrong_type() -> None:
    ensure_failure(
        lambda: check_type(Node, {'type': 5, 'file': 'foo', 'line': (1, 2), 'children': []}),
        LoadWrongType)

    ensure_failure(
        lambda: check_type(Node, {'type': 'node', 'file': 'foo', 'line': (1, 2), 'children': 5}),
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


def test_too_many_fields() -> None:
    ensure_failure(
        lambda: check_type(Node, {
            'type': 'node', 'file': 'foo', 'line': (1, 2), 'children': [], 'extra': True}),
        LoadUnknownField)


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


if __name__ == '__main__':
    test_ensure_failure()
    test_successful()
    test_wrong_type()
    test_wrong_arity()
    test_no_union_variant()
    test_bad_recursive_type()
    test_too_many_fields()
    test_any_types()
    test_unknown_origin_type()
