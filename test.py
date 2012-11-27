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

if __name__ == '__main__':
    unittest.main()
