from numpy.testing import assert_equal

from codetools.blocks.decorators import func2str

def test_func2str():
    expected_lines = "a=1\nb=2\n"

    "dummy string"
    @func2str
    # dummy comment
    def f1():
        a=1
        b=2
    dummy = 3
    assert_equal(f1, expected_lines)

    @func2str
    # dummy comment
    def f1(x):
        a=1
        b=2
    assert_equal(f1, expected_lines)

    @func2str
    # dummy comment
    def f1(x=1):
        a=1
        b=2
    assert_equal(f1, expected_lines)

    @func2str
    def f1(x=1):
        a=1
        b=2
    assert_equal(f1, expected_lines)

    @func2str
    def f1():
        def f1sub():
            pass
        a=1
        b=2
    assert_equal(f1, 'def f1sub():\n    pass\n' + expected_lines)

