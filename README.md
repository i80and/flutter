flutter.py
==========

Example
-------

```
from dataclasses import dataclass
from flutter import checked, check_type
from typing import List


@checked
@dataclass
class Node:
    line: int


@checked
@dataclass
class Parent(Node):
    children: List[Node]


check_type(Parent, {
    'line': 0,
    'children': [{'line': 1}]
})
```
