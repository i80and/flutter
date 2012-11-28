#!/usr/bin/env python3
import unittest
import flutter


class FlutterTests(unittest.TestCase):
    def test_empty(self):
        """A simple test involving an unconstrained argument."""
        doerror = False
        @flutter.check(flutter.Empty(), int)
        def inner(x):
            if doerror:
                return 'a string'
            return 5

        inner(3)
        inner('test')
        inner(None)

        doerror = True
        with self.assertRaises(TypeError):
            inner(3)
    
    def test_readme(self):
        """Test the examples given in the README."""
        doerror = False
        @flutter.check(flutter.Union(int, float),
                       flutter.Function(flutter.Union(int, float), int),
                       flutter.Tuple(int, str))
        def inner(x, f):
            if doerror:
                return (f(x),)
            return (f(x), str(x))

        inner(3, int)
        inner(4.0, int)

        with self.assertRaises(TypeError):
            inner(3, lambda x: str(x))
        with self.assertRaises(TypeError):
            inner('string', 'second string')
        with self.assertRaises(TypeError):
            doerror = True
            inner(3, int)

    def test_iterable(self):
        """Test typed iterables."""
        @flutter.check(flutter.TypedIterable(int), int)
        def inner(x):
            return sum(x)

        inner([1, 2, 3])
        with self.assertRaises(TypeError):
            inner([1, 2, 'foo'])

    def test_container(self):
        """Test typed container."""
        # Note---this is bad practice.  Typically one should not bind a
        # function to a particular concrete type.
        @flutter.check(flutter.TypedContainer(list, int), int)
        def inner(x):
            return sum(x)

        inner([1, 2, 3])
        with self.assertRaises(TypeError):
            inner([1, 2, 'foo'])
        with self.assertRaises(TypeError):
            inner((1, 2, 3,))

    def test_tuple(self):
        """Test tuple types (n-element iterables of exact types)."""
        @flutter.check(flutter.Tuple(int, int, float), flutter.Empty())
        def inner(x):
            pass

        inner((1, 2, 3.5))
        inner([1, 2, 3.5])

        with self.assertRaises(TypeError):
            inner((1, 2))
        with self.assertRaises(TypeError):
            inner(['foo', 2, 3.5])

    def test_aliases(self):
        """Test the simple case of pre-instantiating type specifiers."""
        Number = flutter.Union(int, float)
        @flutter.check(Number, int)
        def inner(x):
            return int(x)

        inner(4)
        inner(3.4)
        with self.assertRaises(TypeError):
            inner('test')

    def test_full_aliases(self):
        """Test pre-instantiating an entire prototype."""
        doerror = False

        FunctionSpecifier = [int, int, flutter.Function(int)]
        @flutter.check(FunctionSpecifier)
        def inner(x, y):
            if doerror:
                return 0

            def adder():
                return x + y
            return adder
        
        inner(1, 2)
        with self.assertRaises(TypeError):
            inner(1, 2.0)

        doerror = True
        with self.assertRaises(TypeError):
            inner(1, 2)

if __name__ == '__main__':
    unittest.main()
