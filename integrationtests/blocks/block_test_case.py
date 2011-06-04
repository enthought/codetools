import re, sys, time, unittest
from compiler.ast import Discard, Module, Name, Stmt
from cPickle import dumps, loads
from StringIO import StringIO

from traits.testing.api import doctest_for_module, skip
from codetools.util.dict import map_values
import codetools.util.graph as graph

import codetools.blocks.block as block
from codetools.blocks.api import Block, Expression

# Extend base class compiler.ast.Node with deep equality
import codetools.blocks.compiler_.ast.deep_equality

class BlockDocTestCase(doctest_for_module(block)):
    pass

class BlockTestCase(unittest.TestCase):

    ### BlockTestCase interface ###############################################

    def assertSimilar(self, a, b):
        'Assert that two blocks are structurally equivalent.'
        a._tidy_ast()
        b._tidy_ast()
        self.assertEqual(str(a.ast), str(b.ast))

    ### Support ###############################################################

    def _base(self, code, inputs, outputs, conditional_outputs,
              dep_graph):
        b = Block(code)

        # Compare inputs and outputs
        self.assertEqual(set(b.inputs), set(inputs))
        self.assertEqual(set(b.outputs), set(outputs))
        self.assertEqual(set(b.conditional_outputs), set(conditional_outputs))

        # Compare dependency graphs: since the real dep_graphs contain crazy
        # block objects, the given dep_graph specifies them by their index in
        # the sequence, e.g.
        #   for code
        #       'a=z; b=f(a,y)'
        #   the given dep_graph should be
        #       { '0':'z',  # Command 0 depends on input z
        #         '1':'0y', # Command 1 depends on command 0 and input y
        #         'a':'0',  # Output a depends on command 0
        #         'b':'1' } # Output b depends on command 1

        # Resolve indices to blocks
        def num_to_block(x):
            '''If x is number-like, lookup the xth block in b.sub_blocks;
            otherwise, leave x unchanged.'''
            try:
                return b.sub_blocks[int(x)]
            except ValueError: # If int(x) fails
                return x
            except TypeError: # In case b doesn't decompose
                return b
        dep_graph = graph.map(num_to_block, dep_graph)

        # Hand-make a trivial dep graph if 'b' doesn't have sub-blocks
        if b.sub_blocks is not None:
            b_dep_graph = b._dep_graph
        else:
            b_dep_graph = {}
            if b.inputs:
                b_dep_graph[b] = b.inputs
            for o in b.all_outputs:
                b_dep_graph[o] = set([b])

        # Compare dep_graphs
        self.assertEqual(map_values(set, b_dep_graph),
                         map_values(set, dep_graph))

    ### Tests: Block API ######################################################

    def test_block_composition(self):
        'Composing Blocks'
        self.assertSimilar(Block('a; b; c'), Block(('a', 'b', 'c')))
        self.assertSimilar(Block('a'), Block(('a')))
        self.assertSimilar(Block(''), Block(()))
        self.assertSimilar(Block('if t: a = b\nc = f(a)'), Block(('if t: a = b', 'c = f(a)')))

    def test_sub_block_manipulation(self):
        'Sub-block manipulation'

        # A block's structure responds to changes in the 'sub_blocks' list
        b = Block('a; b')
        b.sub_blocks.append(Block('c'))
        self.assertSimilar(b, Block('a; b; c'))
        del b.sub_blocks[1]
        self.assertSimilar(b, Block('a; c'))
        b.sub_blocks.reverse()
        self.assertSimilar(b, Block('c; a'))
        b.sub_blocks[0] = Block('b')
        self.assertSimilar(b, Block('b; a'))
        b.sub_blocks = []
        self.assertSimilar(b, Block())
        b.sub_blocks = []
        self.assertSimilar(b, Block())

        # But if we end up with a block that doesn't decompose, 'sub_blocks'
        # goes away!
        b = Block('a; b; c')
        b.sub_blocks.pop()
        self.assertSimilar(b, Block('a; b'))
        self.assertEqual(len(b.sub_blocks), 2)
        b.sub_blocks.pop()
        self.assertSimilar(b, Block('a'))
        self.assertEqual(len(b.sub_blocks), 1)
        b.sub_blocks = [Block('b')]
        self.assertSimilar(b, Block('b'))
        self.assertEqual(len(b.sub_blocks), 1)
        b.sub_blocks = [Block('a'), Block('b')]
        self.assertSimilar(b, Block('a; b'))
        self.assertEqual(len(b.sub_blocks), 2)

        # Note that some seemingly large things don't (currently) decompose:
        block = Block('for x in l:\n  a = f(x)\n  b = g(a)\n  if t: h()')
        self.assertEqual(len(block.sub_blocks), 1)

    def test_ast_policy(self):
        'Policy: Keep tidy ASTs'

        a = Discard(Name('a'))
        empty = Stmt([])

        self.assertEqual(empty, Block('').ast)
        self.assertEqual(empty, Block(empty).ast)
        self.assertEqual(empty, Block(Module(None, empty)).ast)

        self.assertEqual(a, Block('a').ast)
        self.assertEqual(a, Block(a).ast)
        self.assertEqual(a, Block(Stmt([a])).ast)
        self.assertEqual(a, Block(Module(None, Stmt([a]))).ast)

        # Similar, except we don't use strings since Block does its own parsing
        b = Block()
        b.ast = empty
        self.assertEqual(b.ast, empty)
        b.ast = Module(None, empty)
        self.assertEqual(b.ast, empty)
        b.ast = a
        self.assertEqual(b.ast, a)
        b.ast = Stmt([a])
        self.assertEqual(b.ast, a)
        b.ast = Module(None, Stmt([a]))
        self.assertEqual(b.ast, a)

    ### Tests: code analysis ##################################################

    def test_basic_code_analysis(self):
        'Basic code analysis'

        # Multi-letter variable names work fine...
        self._base('foo = bar(baz)',
                   ('bar', 'baz'), ('foo',), (),
                   { '0':['bar', 'baz'], 'foo':'0' })

        # ...but writing single-letter names is more economical
        self._base('a = 0', (), 'a', (), {'a':'0'})
        self._base('a = z', 'z', 'a', (), { '0':'z', 'a':'0' })

    def test_discard(self):
        'Discard'

        # Discards give inputs but no outputs
        self._base('1 + 1', (), (), (), {})
        self._base('1 + x', 'x', (), (), {'0':'x'})

    def test_attributes(self):
        'Attributes'
        self._base('a = z.y', ['z.y'], 'a', (), { '0':['z.y'], 'a':'0' })
        self._base('a.b = z.y', ['z.y'], ['a.b'], (), { '0':['z.y'], 'a.b':'0' })

    def test_function_names(self):
        'Function names'
        # Functions are free variables too
        self._base('a = f(z)', 'fz', 'a', (), { '0':'fz', 'a':'0' })

    def test_binding(self):
        'Binding'
        self._base('a = f(z); b = a', 'fz', 'ab', (),
                   { '0':'fz', '1':'0', 'a':'0', 'b':'1' })
        self._base('a = f(z,g(y),x); b = x', 'fgxyz', 'ab', (),
                   { '0':'fgxyz', '1':'x', 'a':'0', 'b':'1' })
        self._base('a,b,[c,d] = f(z, g(1,y)) + 3; e = b + x; d = h(d)',
                   'fghxyz', 'abcde', (),
                   { '0':'fgyz', '1':'0x', '2':'0h',
                     'a':'0', 'b':'0', 'c':'0', 'd':'2', 'e':'1' })

    def test_conditional_binding(self):
        'Conditional binding'

        self._base('if t: a = 0', 't', (), 'a',
                   { '0':'t', 'a':'0' })
        self._base('if t: a = 0\nif u: a = 1', 'tu', (), 'a',
                   { '0':'t', '1':'0u', 'a':'1' })
        self._base('if t: a = z\nb = a', 'taz', 'b', 'a',
                   { '0':'tza', '1':'0a', 'a':'0', 'b':'1' })
        self._base('b = a\nif t: a = z', 'atz', 'b', 'a',
                   { '0':'a', '1':'taz', 'b':'0', 'a':'1' })
        self._base('a = z\nif t: a = y\nif u: a = x\nb = a', 'ztyux', 'ab', (),
                   { '0':'z', '1':'0ty', '2':'1ux', '3':'2', 'a':'2', 'b':'3' })

    def test_collisions(self):
        'Collisions'
        self._base('a = a', 'a', 'a', (), { '0':'a', 'a':'0' })

    def test_shadowing(self):
        'Shadowing'
        self._base('a = x; a = y', 'xy', 'a', (), { '0':'x', '1':'y', 'a':'1' })

    def test_policy_no_side_effects(self):
        'Policy: no side effects'

        # For block restriction to be useful, we assume that sub-blocks are
        # functions in the mathematical sense: they do nothing more than
        # compute their outputs as a well-defined function of their inputs.
        #
        # Strictly speaking, this means that they can't have side effects --
        # anything like modifying input objects, using global state, or doing
        # I/O. But in practice it's fine if they simply log debugging
        # information since that kind of output doesn't affect the semantics of
        # the block in a meaningful way. What's important is that the
        # sub-blocks' input and output names provide all the information
        # necessary to build a correct dependency graph for the block, and that
        # the block has no effect other than computing its advertised outputs.
        #
        # Python is full of side effects, but if we don't assume mathematically
        # pure functions then we are forced to conclude that any input name we
        # see can be modified -- and yet we are still unable to say anything
        # about the names we can't see! Constructing a correct, non-linear
        # dependency graph is far more difficult if we don't assume purity.

        s1 = 'a = list(z); a += [1,2]; a.append(3)'
        s2 = 'a = f(x)'
        s3 = 'a.foo(z)'
        s4 = 'A.foo(a, z)'

        # Pure
        self._base(s1, 'z', 'a', (), { '0':'z', '1':'0', '2':'1', 'a':'1' })
        self._base(s2, 'fx', 'a', (), { '0':'fx', 'a':'0' })
        self._base(s3, 'az', (), (), { '0':'az' })
        self._base(s4, 'Aaz', (), (), { '0':'Aaz' })

        # Impure: inputs become conditional outputs because they might be
        # modified. (And this only captures effects to names that we can see
        # going in or out of a function call. If 'f()' updates a global
        # variable that affects the behavior of 'g()', we have no way to learn
        # about that dependency.)
        #self._base(s1, 'z', 'a', 'z',
        #           { '0':'z', '1':'0', '2':'1', 'a':'2', 'z':'0' })
        #self._base(s2, 'fx', 'a', 'x', { '0':'fx', 'a':'0', 'x':'0' })
        #self._base(s3, 'az', (), 'az', { '0':'an', 'a':'0', 'z':'0' })
        #self._base(s4, 'Aan', (), 'Aaz',
        #           { '0':'Aaz', 'A':'0', 'a':'0', 'z':'0' })

    @skip
    def test_extractable_inputs(self):
        'Extractable inputs'

        def test(code, extractable_inputs):
            self.assertEqual(Block(code).extractable_inputs,
                             set(extractable_inputs))

        # TODO (current)

        # Basic
        test('a', ())
        test('a = b', ())
        test('a = 0', 'a')
        test('a = b = c = 0', 'abc')
        test('a = b = c = d', ())

        # Sequences
        test('a,b = 0', 'ab')
        test('a = 0,1', 'a')
        test('a,b = 0,1', 'ab')
        test('a,b = [0,1]', 'ab')
        test('[a,b] = [0,1]', 'ab')
        test('[a,(b,c)],d = [0,(1,2)],3', 'abcd')
        test('[a,(b,c)],d = [0,(e,2)],f', 'ac')

    @skip
    def test_extract_inputs(self):
        'Extract inputs'

        def test(code, inputs, expected_code):
            self.assertSimilar(Block(code).extract_inputs(inputs),
                               Block(expected_code))

        def fails(code, inputs):
            self.assertRaises(ValueError, Block(code).extract_inputs, inputs)

        test('a = 0', 'a', 'a = _a_extracted')
        fails('a = b', 'a')
        fails('a = b', 'b')

    def test_tracebacks(self):
        'Tracebacks have correct file names and line numbers'

        # If we want tracebacks to make sense, then the reported file names and
        # line numbers need to associate with the code being executed
        # regardless which block represents and executes the code.

        def test(tb, lineno, filename):
            self.assertEqual(tb.tb_lineno, lineno+1)
            self.assertEqual(tb.tb_frame.f_code.co_filename, filename)

        def tracebacks():
            "A list of the current exception's traceback objects."
            tb = sys.exc_info()[2]
            l = [tb]
            while tb.tb_next is not None:
                tb = tb.tb_next
                l.append(tb)
            return l

        class File(StringIO, object):
            "Extend StringIO with a 'name' attribute."
            def __init__(self, name, *args, **kw):
                super(File, self).__init__(*args, **kw)
                self.name = name

        a = Block(File('foo/a.py', 'y = x'))
        try:
            a.execute({})
        except NameError, e:
            test(tracebacks()[-1], 1, 'foo/a.py')
        del a

        a = Block(File('foo/a.py', 'import sys\ny = x'))
        try:
            a.execute({})
        except NameError, e:
            test(tracebacks()[-1], 2, 'foo/a.py')
        #del a # (use below in 'Compose')

        b = Block(File('foo/b.py',
                "import re\nl=re.findall('a(.*?)a', 'abacada')\nx = l[2]"))
        try:
            b.execute({})
        except IndexError, e:
            test(tracebacks()[-1], 3, 'foo/b.py')
        #del b # (use below in 'Compose')

        # Compose
        c = Block((a,b))
        try:
            c.execute({})
        except NameError, e:
            test(tracebacks()[-1], 2, 'foo/a.py')
        try:
            c.execute({'x':0})
        except IndexError, e:
            test(tracebacks()[-1], 3, 'foo/b.py')
        del a,b,c

        # Restrict
        a = Block(File('foo/a.py', 'a = 0\nb = 1\nc = 2/a'))
        try:
            a.restrict(outputs='c').execute({})
        except ZeroDivisionError, e:
            test(tracebacks()[-1], 3, 'foo/a.py')
        del a

        # Throw out a sub-block
        a = Block(File('foo/a.py', 'a = 0\nb = 1\nc = 2/a'))
        a.sub_blocks.pop(1)
        try:
            a.execute({})
        except ZeroDivisionError, e:
            test(tracebacks()[-1], 3, 'foo/a.py')
        del a

        # Swap sub-blocks between blocks
        a = Block(File('foo/a.py', 'a = 0\nb = 1'))
        b = Block(File('foo/b.py', 'c = 2\nd = x'))
        a.sub_blocks = b.sub_blocks
        try:
            a.execute({})
        except NameError, e:
            test(tracebacks()[-1], 2, 'foo/b.py')
        a.sub_blocks = b.sub_blocks[:]
        try:
            a.execute({})
        except NameError, e:
            test(tracebacks()[-1], 2, 'foo/b.py')
        del a,b

    def test_construction(self):
        'Construction'
        pass # TODO

    def test_caching_dep_graph_restrict(self):
        "Caching: '_dep_graph', 'restrict'"

        # '_dep_graph' determines the behavior of 'restrict', so we can test
        # them together.

        b = Block('a=2; b=a; z=a')
        self.assertSimilar(b.restrict(outputs='z'), Block('a=2; z=a'))
        b.sub_blocks = [Block('z=0')]
        self.assertSimilar(b.restrict(outputs='z'), Block('z=0'))

        b = Block('a=2; b=a; z=a')
        self.assertSimilar(b.restrict(outputs='z'), Block('a=2; z=a'))
        b.ast = Block('z=0').ast
        self.assertSimilar(b.restrict(outputs='z'), Block('z=0'))

    def test_caching_code(self):
        "Caching: '_code'"

        b,c = Block('a=2'), {}
        b._code
        b.ast = Block('a=3').ast
        b.execute(c)
        self.assertEqual(c['a'], 3)

        b,c = Block('a=2'), {}
        b._code
        b.sub_blocks = [Block('a=3')]
        b.execute(c)
        self.assertEqual(c['a'], 3)

        b,c = Block('a=3; a=2'), {}
        b._code
        b.sub_blocks.pop()
        b.execute(c)
        self.assertEqual(c['a'], 3)

        b,c = Block(''), {}
        b._code
        b.sub_blocks.append(Block('a=3'))
        b.sub_blocks = [Block('a=3')]
        b.execute(c)
        assert 'a' in c

    def test_optimization_no_filenames_in_tracebacks(self):
        'Optimization: No filenames in tracebacks'
        b = Block('import operator\n'
                  'x,d = 2,{}\n'
                  'for i in range(10):\n'
                  '  d[i] = repr(i)\n'
                  '  x *= 2\n'
                  'sum = lambda l, add=operator.add: reduce(add, l)\n'
                  'd = (sum(d.keys()), sum(d.values()))\n',
                  no_filenames_in_tracebacks = True)
        c = {}
        b.execute(c)
        assert c['x'] == 2**11
        assert c['d'] == (9*10/2, '0123456789')

class ExpressionTestCase(unittest.TestCase):

    ### Support ###############################################################

    def _base(self, code, value, inputs, **mapping):

        e = Expression.from_string(code)

        self.assertEqual(set(inputs), set(e.inputs))
        self.assertEqual(set([]), set(e.outputs))
        self.assertEqual(value, e.evaluate(dict(mapping)))

    ### Tests #################################################################

    def test(self):
        'Expressions'
        self._base('1+2', 3, ())
        self._base('a+2', 3, 'a', a=1)
        self._base('a+b', 3, 'ab', a=1, b=2)
        self.assertRaises(SyntaxError, Expression.from_string, 'a=b')

class BlockRestrictionTestCase(unittest.TestCase):

    ### Support ###############################################################

    def assertSimilar(self, a, b):
        'Assert that two blocks are structurally equivalent.'
        a._tidy_ast()
        b._tidy_ast()
        self.assertEqual(str(a.ast), str(b.ast))

    def _base(self, code, inputs, outputs, *results):

        # Convert results to a string if necessary
        def try_join(x):
            if not isinstance(x, basestring):
                return '\n'.join(x)
            else:
                return x
        results = map(try_join, results)

        # Avoid empty discard statements at the end of 'results'
        results = [ re.sub(';*$', '', r) for r in results ]

        # Make sure code's sub-block is one of the given results (restrict
        # isn't deterministic on parallelizable code)
        restricted = Block(code).restrict(inputs=inputs, outputs=outputs)
        if results == ['']:
            self.assertSimilar(restricted, Block(()))
        else:
            self.assertTrue(restricted.ast in [Block(r).ast for r in results])

    ### Tests #################################################################

    def test_restrict_on_nested_blocks(self):
        b1 = Block('a=0;b=a+1')
        b2 = Block('x=99;z=x-1')
        composite=Block([b1,b2])

        self.assertSimilar( Block('a=0'),
                            composite.restrict(outputs=['a']))
        self.assertSimilar( Block('x=99'),
                            composite.restrict(outputs=['x']))

    def test_restrict(self):
        'Restricted blocks'

        # This AST has a nice shape:
        #
        #  z     y
        #  |     |
        #  -     -
        # |f|   |g|
        #  -     -
        #   a\ /b b\
        #     -     -
        #    |h|   |k|
        #     -     -
        #     |     |
        #     c     d
        #
        code = 'a=f(z)', 'b=g(y)', 'c=h(a,b)', 'd=k(b)'

        # All the sub-blocks (except the empty one)
        f = (code[0],)
        g = (code[1],)
        h = (code[2],)
        k = (code[3],)
        fh = f + h
        gh = g + h
        gk = g + k
        fg = [f + g, g + f]
        hk = [h + k, k + h]
        fk = [f + k, k + f]
        fgh = [ b + h for b in fg ]
        ghk = [ g + b for b in hk ]
        fgk = [f + gk, gk + f]
        fhk = [fh + k, k + fh, f + k + h]
        fghk = [ b1 + b2 for b1 in fg for b2 in hk ] + [g + k + f + h]

        # One-sided
        self._base(code, 'z', (), fh)
        self._base(code, 'y', (), *ghk)
        self._base(code, 'zy', (), *fghk)
        self._base(code, (), 'a', *f)
        self._base(code, (), 'b', *g)
        self._base(code, (), 'c', *fgh)
        self._base(code, (), 'd', gk)
        self._base(code, (), 'ab', *fg)
        self._base(code, (), 'abc', *fgh)
        self._base(code, (), 'abcd', *fghk)

        # Intersections
        self._base(code, 'z', 'c', fh)
        self._base(code, 'z', 'd', ()) # No intersection
        self._base(code, 'z', 'cd', fh)
        self._base(code, 'y', 'c', gh) # The interesting case
        self._base(code, 'y', 'd', gk)
        self._base(code, 'y', 'cd', *ghk)
        self._base(code, 'zy', 'c', *fgh)
        self._base(code, 'zy', 'd', gk)
        self._base(code, 'zy', 'cd', *fghk)

    def test_restrict_conditional(self):
        'Restricted blocks with conditional outputs'

        code = 'if t: a = 0', 'b = a'
        self._base(code, (), 'a', code[0])
        self._base(code, (), 'b', code)
        self._base(code, 'a', (), code)
        self._base(code, 't', (), code)

        code = 'a = 0', 'if t: a = 1\nelse: a = 2', 'b = a'
        self._base(code, (), 'a', code[1])
        self._base(code, (), 'b', code[1:])
        self._base(code, 't', (), code[1:])

        code = 'a = z', 'a = y', 'if t: a = x', 'if u: a = w', 'b = a'
        self._base(code, (), 'a', code[1:4])
        self._base(code, (), 'b', code[1:])
        self._base(code, 't', (), code[2:])
        self._base(code, 'u', (), code[3:])
        self._base(code, 'w', (), code[3:])
        self._base(code, 'x', (), code[2:])
        self._base(code, 'y', (), code[1:])
        self._base(code, 'z', (), code[0])

    def test_errors(self):
        'Errors for block restriction'

        # Note: 'a' can be passed as a input, which should return
        # a trivial subblock. This is due to supporting intermediate
        # inputs

        b = Block('a = b')
        self.assertRaises(ValueError, b.restrict, outputs='b')
        self.assertRaises(ValueError, b.restrict, inputs='z')
        self.assertRaises(ValueError, b.restrict, outputs='z')
        self.assertRaises(ValueError, b.restrict)

    def test_imports(self):
        'restrict blocks containing imports'

        # Test 'from' syntax
        b = Block('from math import sin, pi\n'\
                  'b=sin(pi/a)\n' \
                  'd = c * 3.3')

        sub_block = b.restrict(inputs=('a'))
        self.assertEqual(sub_block.inputs, set(['a']))
        self.assertEqual(sub_block.outputs, set(['b']))
        self.assertEqual(sub_block.fromimports, set(['pi', 'sin']))

        context = {'a':2, 'c':0.0}
        sub_block.execute(context)
        self.assertTrue(context.has_key('b'))
        self.assertEqual(context['b'], 1.0)

        # Test 'import' syntax
        b = Block('import math\n'\
                  'b=math.sin(math.pi/a)\n' \
                  'd = c * 3.3')

        sub_block = b.restrict(inputs=('a'))
        self.assertEqual(sub_block.inputs, set(['a']))
        self.assertEqual(sub_block.outputs, set(['b']))
        self.assertEqual(sub_block.fromimports, set(['math']))

        context = {'a':2, 'c':0.0}
        sub_block.execute(context)
        self.assertTrue(context.has_key('b'))
        self.assertEqual(context['b'], 1.0)

    def test_intermediate_inputs(self):
        """ restrict blocks with inputs which are intermediates """
        block = Block('c = a + b\n'\
                  'd = c * 3')

        sub_block = block.restrict(inputs=('c'))
        self.assertEqual(sub_block.inputs, set(['c']))
        self.assertEqual(sub_block.outputs, set(['d']))

        context = {'a':1, 'b':2}
        block.execute(context)
        self.assertEqual(context['c'], 3)
        self.assertEqual(context['d'], 9)

        context = {'c':10}
        sub_block.execute(context)
        self.assertEqual(context['c'], 10)
        self.assertEqual(context['d'], 30)


        context = {'d':15}
        sub_block = block.restrict(inputs=('d'))
        self.assertEqual(sub_block.inputs, set([]))
        self.assertEqual(sub_block.outputs, set([]))
        sub_block.execute(context)
        self.assertEqual(context['d'], 15)

    def test_intermediate_inputs_with_highly_connected_graph(self):
        """ restrict blocks with inputs which are intermediates on a highly connected graph"""

        code =  "c = a + b\n" \
                "d = c * 3\n" \
                "e = a * c\n" \
                "f = d + e\n" \
                "g = e + c\n" \
                "h = a * 3"

        block = Block(code)
        sub_block = block.restrict(inputs=('c'))
        self.assertEqual(sub_block.inputs, set(['a', 'c']))
        self.assertEqual(sub_block.outputs, set(['d', 'e', 'f', 'g']))

        context = {'a':1, 'b':2}
        block.execute(context)
        self.assertEqual(context['c'], 3)
        self.assertEqual(context['d'], 9)
        self.assertEqual(context['e'], 3)
        self.assertEqual(context['f'], 12)
        self.assertEqual(context['g'], 6)

        context = {'a':1, 'c':10}
        sub_block.execute(context)
        self.assertEqual(context['c'], 10)
        self.assertEqual(context['d'], 30)
        self.assertEqual(context['e'], 10)
        self.assertEqual(context['f'], 40)
        self.assertEqual(context['g'], 20)

    def test_intermediate_inputs_and_outputs(self):
        """ restrict blocks with inputs and outputs which are intermediates """

        code =  "c = a + b\n" \
                "d = c * 3\n" \
                "e = a * c\n" \
                "f = d + e\n" \
                "g = e + c\n" \
                "h = a * 3"

        block = Block(code)
        sub_block = block.restrict(inputs=('c'), outputs=('e', 'g'))
        self.assertEqual(sub_block.inputs, set(['a', 'c']))
        self.assertEqual(sub_block.outputs, set(['e', 'g']))

        context = {'a':1, 'b':2}
        block.execute(context)
        self.assertEqual(context['c'], 3)
        self.assertEqual(context['e'], 3)
        self.assertEqual(context['g'], 6)

        context = {'a':1, 'c':10}
        sub_block.execute(context)
        self.assertEqual(context['c'], 10)
        self.assertEqual(context['e'], 10)
        self.assertEqual(context['g'], 20)

    def test_inputs_are_imports(self):
        """ restrict blocks with inputs which are imported """

        code =  "from numpy import arange\n" \
                "x = arange(0, 10, 0.1)\n" \
                "c1 = a * a\n" \
                "x1 = x * x\n" \
                "t1 = c1 *x1\n" \
                "t2 = b * x\n" \
                "t3 = t1 + t2\n" \
                "y = t3 + c\n"

        block = Block(code)
        sub_block = block.restrict(inputs=['arange'])
        self.assertEqual(sub_block.inputs, set(['c1', 'b', 'c']))
        self.assertEqual(sub_block.outputs, set(['x', 'x1', 't1',
                                                 't2', 't3', 'y']))

    def test_inputs_are_dependent_outputs(self):
        """ restrict blocks with inputs which are intermediates and outputs"""

        code =  "t2 = b * 2\n" \
                "t3 = t2 + 3\n"

        block = Block(code)
        sub_block = block.restrict(inputs=['t2', 't3'])

    def test_heirarchical_inputs(self):
        """ restrict blocks with inputs which are nested """

        code =  "from numpy import arange\n" \
                "x = arange(0, 10, 0.1)\n" \
                "c1 = inner.a * inner.a\n" \
                "x1 = x * x\n" \
                "t1 = c1 *x1\n" \
                "t2 = inner.b * x\n" \
                "t3 = t1 + t2\n" \
                "y = t3 + inner.c\n"

        block = Block(code)
        sub_block = block.restrict(inputs=['inner.a'])
        self.assertEqual(sub_block.inputs, set(['inner.a', 'inner.c', 'x1', 't2']))
        self.assertEqual(sub_block.outputs, set(['y', 'c1', 't3', 't1']))

        self.assertEqual(len(sub_block.sub_blocks), 5)
        self.assertSimilar(sub_block.sub_blocks[0], Block('from numpy import arange'))
        self.assertSimilar(sub_block.sub_blocks[1], Block('c1 = inner.a * inner.a'))
        self.assertSimilar(sub_block.sub_blocks[2], Block('t1 = c1 *x1'))
        self.assertSimilar(sub_block.sub_blocks[3], Block('t3 = t1 + t2'))
        self.assertSimilar(sub_block.sub_blocks[4], Block('y = t3 + inner.c'))


        code =  "from numpy import arange\n" \
                "x = arange(0, 10, 0.1)\n" \
                "c1 = outter.a * outter.a\n" \
                "x1 = x * x\n" \
                "t1 = c1 *x1\n" \
                "t2 = outter.inner.b * x\n" \
                "t3 = t1 + t2\n" \
                "y = t3 + outter.inner.c\n"

        block = Block(code)
        sub_block = block.restrict(inputs=['outter.a'])
        self.assertEqual(sub_block.inputs, set(['outter.a', 'outter.inner.c', 'x1', 't2']))
        self.assertEqual(sub_block.outputs, set(['y', 'c1', 't3', 't1']))

        self.assertEqual(len(sub_block.sub_blocks), 5)
        self.assertSimilar(sub_block.sub_blocks[0], Block('from numpy import arange'))
        self.assertSimilar(sub_block.sub_blocks[1], Block('c1 = outter.a * outter.a'))
        self.assertSimilar(sub_block.sub_blocks[2], Block('t1 = c1 *x1'))
        self.assertSimilar(sub_block.sub_blocks[3], Block('t3 = t1 + t2'))
        self.assertSimilar(sub_block.sub_blocks[4], Block('y = t3 + outter.inner.c'))



class BlockPickleTestCase(unittest.TestCase):

    def test_pickle(self):
        'Pickling'

        strings = [
            ''
            'a=b',
            'a=b;c=d',
            'a=f(z); b=g(y); c=h(a,b); d=k(b)',
        ]

        for s in strings:
            b = Block(s)
            self.assertEqual(loads(dumps(b)), b, '(where s = %r)' % s)

class BlockRegressionTestCase(unittest.TestCase):

    def test_cyclic_dep_graph(self):
        "Regression: Don't make cyclic dep graphs"
        # When an input and output name are the same, we used to represent them
        # identically in the dep graph, making it cyclic (and wrong anyway)
        try:
            # (';' appends an empty 'Discard' statement to the block, which
            # gives it multiple sub-blocks, which forces 'restrict' to run
            # non-trivially)
            Block('a = a;').restrict(inputs=['a'])
        except graph.CyclicGraph:
            self.fail()

class BlockRegressionTestCase(unittest.TestCase):

    @skip
    def test_dep_graph_exists_for_line_of_code(self):
        """ Does block treat 1 func blocks like multi-func blocks.

            It doesn't appear that simple blocks are forcing updates
            to the dep_graph.  One func graphs Should be the same as
            multi-line ones (I think).  Without this, we have to
            always check for None and special case that code path in
            all the processing tools.

            fixme: I (eric) haven't examined this very deeply, it
                   just cropped up in some of my code.  This test
                   is a reminder that we need to either fix it or
                   verify that we don't want to fix it.
        """
        block = Block('b = foo(a)\nc=bar(b)\n')
        self.assertTrue(block._dep_graph is not None)

        block = Block('b = foo(a)\n')
        self.assertTrue(block._dep_graph is not None)

if __name__ == '__main__':
    unittest.main(argv=sys.argv)
