flutter.py
==========

Example
-------

.. code-block:: python

   from dataclasses import dataclass, field
   from flutter import checked, check_type
   from typing import List


   @checked
   @dataclass
   class Node:
       line: int


   @checked
   @dataclass
   class Parent(Node):
       children: List[Node] = field(default_factory=list)


   assert check_type(Parent, {
       'line': 0,
       'children': [{'line': 1}]
   }) == Parent(line=0, children=[Node(1)])

   assert check_type(Parent, {
       'line': 10
   }) == Parent(line=10, children=[])
