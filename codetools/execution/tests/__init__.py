from unittest import SkipTest

import six


def setup_package():
    if six.PY3:
        raise SkipTest("codetools.blocks not ported to Python 3")
