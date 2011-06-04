import unittest
from traits.testing.api import doctest_for_module
import codetools.util.dict as dict

class DictDocTestCase(doctest_for_module(dict)):
    pass

if __name__ == '__main__':
    import sys
    unittest.main(argv=sys.argv)
