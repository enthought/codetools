from compiler import parse
from compiler.ast import Node
from copy import deepcopy
import sys, unittest

from enthought.testing.api import doctest_for_module
from enthought.util.functional import partial
from enthought.util.sequence import all
from enthought.util.tree import flatten, tree_zip

import enthought.numerical_modeling.workflow.block.analysis as analysis
from enthought.numerical_modeling.workflow.block.analysis import (
    ConstAssignExtractor, Transformer, free_vars, local_vars,
    conditional_local_vars,
)
from enthought.numerical_modeling.workflow.block.compiler_.ast.api import \
    similar
from enthought.numerical_modeling.workflow.block.block import Block

class AnalysisDocTestCase(doctest_for_module(analysis)):
    pass

class AnalysisTestMixin:
    def assertSimilar(self, a, b):
        'Assert that two ASTs are structurally equivalent.'
        self.assert_(similar(a, b), '%s != %s' % (a,b))
    def assertNotSimilar(self, a, b):
        self.failIf(similar(a, b), '%s == %s' % (a,b))

class NameAnalysisTestMixin:
    def _base(self, code, free, locals=(), conditional_locals=()):
        ast = parse(code)
        self.assertEqual(set(free), set(free_vars(ast)))
        self.assertEqual(set(locals), set(local_vars(ast)))
        self.assertEqual(set(conditional_locals),
                         set(conditional_local_vars(ast)))

class NameAnalysisTestCase(unittest.TestCase, NameAnalysisTestMixin):

    def test_basic(self):
        'Basic'

        # Multi-letter variable names work fine...
        self._base('foo = bar(baz)', ['bar', 'baz'], ['foo'])

        # ...but writing single-letter names is more economical
        self._base('a = 0', (), 'a')
        self._base('a = z', 'z', 'a')

        # Note that function names are free variables, too
        self._base('a = f(z)', 'fz', 'a')

    def test_binding_occurrances(self):
        'Binding occurrances'

        # Python Reference Manual, 4.1 Naming and Binding:
        #
        #   The following constructs bind names: formal parameters to
        #   functions, import statements, class and function definitions (these
        #   bind the class or function name in the defining block), and targets
        #   that are identifiers if occurring in an assignment, for loop
        #   header, or in the second position of an except clause header. The
        #   import statement of the form ``"from ...import *"'' binds all names
        #   defined in the imported module, except those beginning with an
        #   underscore. This form may only be used at the module level.

        # "formal parameters to functions"
        #self._base('def f(a): a', (), 'f')
        #self._base('def f(a): b', 'b', 'f')
        #self._base('def f(a=b): pass', 'b', 'f')
        self._base('lambda a: a', (), ())
        self._base('lambda a: b', 'b', ())
        self._base('lambda a=b: a', 'b', ())
        self._base('lambda a=b: c', 'bc', ())
        # (Boundary cases)
        #self._base('def f(f): pass', (), 'f')
        #self._base('def f(a=a): pass', 'a', 'f')
        #self._base('def f(f=f): pass', 'f', 'f')
        self._base('lambda a=a: a', 'a', ())
        self._base('lambda a=a: b', 'ab', ())

        # "import statements"
        self._base('import a', (), 'a')
        self._base('import a as b', (), 'b')
        self._base('from a import b,c', (), 'bc')
        self._base('from a import *', (), ()) # Any good way to handle this?

        # "class and function definitions"
        #self._base('def f(): pass', (), 'f')
        #self._base('class C: pass', (), 'C')
        # (Boundary cases)
        #self._base('def f(f): pass', (), 'f')
        #self._base('@f\ndef f(): pass', 'f', 'f')
        #self._base('class C(C): pass', 'C', 'C')

        # "targets that are identifiers if occurring in an assignment"
        self._base('a = 1', (), 'a')
        self._base('a,b = 1', (), 'ab')
        self._base('a,(b,c) = 1', (), 'abc')
        self._base('a,[b,c] = 1', (), 'abc')
        self._base('a,[(b,c),d] = 1', (), 'abcd')
        # (Boundary cases)
        self._base('a = a', 'a', 'a')

        # "for loop header"
        self._base('for i in []: pass', (), (), 'i')
        # (Boundary cases)
        self._base('for a in a: pass', 'a', (), 'a')
        self._base('for a in a: pass\nelse: pass', 'a', (), 'a')

        # "second position of an except clause header"
        self._base('try: pass\nexcept t, e: pass', 't', (), 'e')
        # (Boundary cases)
        self._base('try: pass\nexcept e, e: pass', 'e', (), 'e')

        # Also: list comprehensions and generator expressions
        self._base('[a for a in b]', 'b', (), 'a')
        self._base('(a for a in b)', 'b', (), 'a')
        # (Boundary cases)
        self._base('[a for a in a]', 'a', (), 'a')
        self._base('(a for a in a)', 'a', (), 'a')

    def test_binding(self):
        'Binding'
        self._base('a = 0; a', (), 'a')
        self._base('a = f(z); b = a', 'fz', 'ab')
        self._base('a = f(z,g(y),x); b = x', 'fgxyz', 'ab')
        self._base('f,b,[h,d] = f(z, g(1,y)) + 3; e = b + x; d = h(d)',
                   'fgxyz', 'bdefh')

    def test_imports(self):
        "'import'"
        self._base('import a', (), 'a')
        self._base('import a as b', (), 'b')
        self._base('import a.b', (), 'a')
        self._base('import a.b as c', (), 'c')
        self._base('from a import b,c', (), 'bc')
        self._base('from a.b import c,d', (), 'cd')
        self._base('from a import *', (), ()) # (Any good way to handle '*'?)
        self._base('from a.b import *', (), ())

    def test_augmented_assignment(self):
        'Augmented assignment'
        
        equivalent_pairs = (
            ('a += b', 'a = a + b'),
            ('a |= b - c', 'a = a | (b - c)'),
            ('a.b += c.d', 'a.b = a.b + c.d'),
            ('a[i] += b[j]', 'a[i] = a[i] + b[j]'),
        )

        for c1,c2 in equivalent_pairs:
            ast1, ast2 = parse(c1), parse(c2)
            self.assertEqual(free_vars(ast1), free_vars(ast2))
            self.assertEqual(local_vars(ast1), local_vars(ast2))
            self.assertEqual(conditional_local_vars(ast1),
                             conditional_local_vars(ast2))

    def test_attributes(self):
        'Attributes'
        self._base('a = z.y', ['z.y'], 'a')
        self._base('a.b = z.y', ['z.y'], ['a.b'])

    def test_lambdas(self):
        "'lambda'"
        self._base('lambda a: lambda b: (a,b)', '', '')
        self._base('lambda a: lambda b=c: (a,b)', 'c', '')

    def test_builtins(self):
        'Built-in names'
        self._base('None, len, list, cmp, open, id, str, sin', ['sin'], [])
        self._base('id = id', [], ['id'])

    def test_collisions(self):
        'Collisions'
        self._base('a = a', 'a', 'a')

    def test_shadowing(self):
        'Shadowing'
        self._base('a = x; a = y', 'xy', 'a')

    def test_discard(self):
        'Discard statements'
        self._base('1 + 1', ())
        self._base('1 + x', 'x')

    def test_if(self):
        "'if'"
        # 'if' might produce unconditional locals
        self._base('if t: a = 0', 't', (), 'a')
        self._base('if t: pass\nelse: a = 0', 't', (), 'a')
        self._base('if t: a = 0\nelse: a = 1', 't', 'a', ())
        self._base('if t: a = 0\nelif t: a = 1', 't', (), 'a')
        self._base('if t: pass\nelif t: a = 0\nelse: pass', 't', (), 'a')
        self._base('if t: a = 0\nelif t: a = 1\nelse: a = 2', 't', 'a', ())

    def test_for(self):
        "'for'"
        # 'for' rarely produces unconditional locals
        self._base('for e in l: pass', 'l', (), 'e')
        self._base('for e in l: a = 0', 'l', (), 'ae')
        self._base('for e in l: a = 0\nelse: a = 1', 'l', (), 'ae')
        self._base('for e in l: pass\nelse: e = 0', 'l', 'e', ())
        self._base('for e in l: e = 0\nelse: e = 1', 'l', 'e', ())
        self._base('for e in l: e = 0', 'l', (), 'e')

    def test_while(self):
        "'while'"
        # 'while' can't produce unconditional locals
        self._base('while t: a = 0', 't', (), 'a')
        self._base('while t: a = 0\nelse: a = 1', 't', (), 'a')
        self._base('while t: pass\nelse: a = 1', 't', (), 'a')

    def test_tryexcept(self):
        "'try'/'except'/'else'"
        # 'try'/'except' rarely produces unconditional locals

        self._base('try: a = 0\nexcept: pass', (), (), 'a')
        self._base('try: a = 0\nexcept t: pass', 't', (), 'a')
        self._base('try: a = 0\nexcept t,e: pass', 't', (), 'ae')
        self._base('try: e = 0\nexcept t,e: pass', 't', 'e', ())

        self._base('try: pass\nexcept: pass\nelse: a = 0', (), (), 'a')
        self._base('try: pass\nexcept t: pass\nelse: a = 0', 't', (), 'a')
        self._base('try: pass\nexcept t,e: pass\nelse: a = 0', 't', (), 'ae')
        self._base('try: pass\nexcept t,e: pass\nelse: e = 0', 't', 'e', ())

        self._base('try: a = 0\nexcept: pass', (), (), 'a')
        self._base('try: pass\nexcept: a = 0', (), (), 'a')
        self._base('try: a = 0\nexcept: a = 1', (), 'a', ())

        self._base('try: a = 0\nexcept: pass\nelse: pass', (), (), 'a')
        self._base('try: pass\nexcept: a = 0\nelse: pass', (), (), 'a')
        self._base('try: pass\nexcept: pass\nelse: a = 0', (), (), 'a')
        self._base('try: a = 0\nexcept: pass\nelse: a = 0', (), (), 'a')
        self._base('try: a = 0\nexcept: a = 1\nelse: pass', (), 'a', ())
        self._base('try: pass\nexcept: a = 1\nelse: a = 0', (), 'a', ())
        self._base('try: a = 0\nexcept: a = 1\nelse: a = 0', (), 'a', ())
        self._base('try: e = 0\nexcept t,e: pass\nelse: pass', 't', 'e', ())
        self._base('try: pass\nexcept t,e: pass\nelse: e = 0', 't', 'e', ())

    def test_tryfinally(self):
        "'try'/'finally'"
        # 'try'/'finally' often produces unconditional locals
        self._base('try: a = 0\nfinally: pass', (), (), 'a')
        self._base('try: pass\nfinally: a = 0', (), 'a', ())

    def test_listcomp_and_genexpr(self):
        'List comprehensions, generator expressions'
        # List comprehensions and generator expressions only produce
        # unconditional locals
        for code, free, local, conditional_local in (

            ('a for b in c if d', 'acd', (), 'b'),
            ('x for x in l if x', 'l', (), 'x'),
            ('f for x in x if t', 'ftx', (), 'x'),
            ('x for x in x if x', 'x', (), 'x'),
            ('a for b in c if d for e in f if g if h', 'acdfgh', (), 'be'),

            ('x for (x,i) in enumerate(l) if p(i) and q(x)', 'lpq', (), 'xi'),
            ('(a,b) for a in range(n) for b in range(n) if gcd(a,n)==gcd(b,n)',
             ['n', 'gcd'], (), 'ab'),

            ):
            self._base('[%s]' % code, free, local, conditional_local)
            self._base('(%s)' % code, free, local, conditional_local)

    def test_conditional_locals(self):
        'Conditional local variables'

        # Conditional + conditional -> conditional
        self._base('for a in []: pass\nwhile False: a = 0', (), (), 'a')
        self._base('if False: a = 0\ntry: a = 1\nfinally: b = 2', (), 'b', 'a')

        # Conditional + unconditional -> unconditional
        self._base('a = 0\nif t: a = 1', 't', 'a', ())
        self._base('if t: a = 0\na = 1', 't', 'a', ())

        # Conditional locals don't bind free variables
        self._base('a = 0\nb = a', (), 'ab')
        self._base('if t: a = 0\nb = a', 'ta', 'b', 'a')
        self._base('if t: a = 0\na = 1\nb = a', 't', 'ab')
        self._base('a = 0\nif t: a = 0\nb = a', 't', 'ab')

    def test_combinations(self):
        'Arbitrary combinations of statements'

        # TODO Add some arbitrary combinations of statements

        # Regression: These catch a dumb mistake I made in gathering free names
        # outside of 'visitName'
        self._base('a = 0; a += 1', (), 'a', ())
        self._base('a = 0\nif t: b = a', 't', 'a', 'b')
        
    def test_function_positional_args(self):
        code =  "a = 1.0\n" \
                "def test_func(c, d):\n" \
                "    e = c + 4\n" \
                "    f = d + 4\n" \
                "    return e*f\n" \
                "m = test_func(a, b)"
                
        block = Block(code)
        self.assertEqual(len(block.sub_blocks), 3)
        self.assertEqual(block.inputs, set(['b']))
        self.assertEqual(block.all_outputs, set(['a', 'm', 'test_func']))
        self.assertEqual(block.conditional_outputs, set([]))
        self.assertEqual(block.outputs, set(['a', 'm', 'test_func']))
                         
    def test_function_varargs_args(self):
        code =  "a = 1.0\n" \
                "def test_func(*varargs):\n" \
                "    e = varargs[0] + 4\n" \
                "    f = varargs[1] + 4\n" \
                "    return e*f\n" \
                "m = test_func(a, b)"
                

        def test_raises(code):
            block = Block(code)
            
        self.assertRaises(TypeError, test_raises, code)

    def test_function_kwargs_args(self):
        code =  "a = 1.0\n" \
                "def test_func(c, d):\n" \
                "    e = c + 4\n" \
                "    f = d + 4\n" \
                "    return e*f\n" \
                "m = test_func(d=a, c=b)"

        def test_raises(code):
            block = Block(code)

        try:
            import nose
        except:
            assert(False)

        raise nose.SkipTest("inputs do not get mapped correctly, but we need keyword support for decorators")
            
        self.assertRaises(ValueError, test_raises, code)

        # keywords might be supported in the future, just not yet
        if (True):
            block = Block(code)
            self.assertEqual(len(block.sub_blocks), 3)
            self.assertEqual(block.inputs, set(['b', 'test_func']))
            self.assertEqual(block.all_outputs, set(['a', 'm']))
            self.assertEqual(block.conditional_outputs, set([]))
            self.assertEqual(block.outputs, set(['a', 'm']))
                
    def test_function_kwargs_dict_args(self):
        code =  "a = 1.0\n" \
                "def test_func(**kwargs):\n" \
                "    e = kwargs['c'] + 4\n" \
                "    f = kwargs['d'] + 4\n" \
                "    return e*f\n" \
                "m = test_func(a=a, b=b)"
                
        def test_raises(code):
            block = Block(code)
            
        self.assertRaises(TypeError, test_raises, code)



    def test_function_default_args(self):
        code =  "a = 1.0\n" \
                "def test_func(c, d=1):\n" \
                "    e = c + 4\n" \
                "    f = d + 4\n" \
                "    return e*f\n" \
                "m = test_func(b)"
                
        block = Block(code)
        self.assertEqual(len(block.sub_blocks), 3)
        self.assertEqual(block.inputs, set(['b']))
        self.assertEqual(block.all_outputs, set(['a', 'm', 'test_func']))
        self.assertEqual(block.conditional_outputs, set([]))
        self.assertEqual(block.outputs, set(['a', 'm', 'test_func']))

class TransformTestCase(unittest.TestCase, AnalysisTestMixin):

    def _base(self, transformer, code, expected, **kw):
        t = transformer.transform(parse(code))
        self.assertSimilar(t, parse(expected))
        for k in kw:
            self.assertEqual(getattr(transformer, k), kw[k])

    def test_transformer_base_class(self):
        'Transformer base class'

        test = partial(self._base, Transformer())

        # Transformer.transform doesn't change anything
        test('a = 0', 'a = 0')
        test('a = b', 'a = b')
        test('if t == u-1: a = b,f(c)', 'if t == u-1: a = b,f(c)')
        # ...

        # Transformer.transform makes deep copies by default
        code = 'if t == u: a,b = [1]+[2]\nreturn sum(b,a)'
        a = parse(code)
        b = Transformer().transform(a)
        b.node.nodes[1] = parse('yield x').node.nodes[0]
        b.node.nodes[0].tests[0][0].ops[0] = parse('t > 0').node.nodes[0].expr
        b.node.nodes[0].tests[0][1].nodes[0].expr.left.nodes[0] = 5
        self.assertNotSimilar(b, parse(code))
        self.assertSimilar(a, parse(code))

    def test_extract_constant_assignments(self):
        'Extract constant assignments'

        def test(code, expected, const_for):
            self._base(ConstAssignExtractor(), code, expected,
                       const_for=const_for)

        def fails(code):
            self.assertRaises(SyntaxError,
                              ConstAssignExtractor().transform, parse(code))

        test('a = 0', 'a = __a', { '__a':0 })
        test('a = b; a = 0', 'a = b; a = __a', { '__a':0 })
        test('a = b = 0', 'a = b = __b', { '__b':0 })
        test('b = a = 0', 'b = a = __a', { '__a':0 })
        test('a,b = 0,1', 'a,b = __a, __b', { '__a':0, '__b':1 })
        test('l = a,b = [0,1]', 'l = a,b = [__a, __b]', { '__a':0, '__b':1 })
        test('a,b = l = [0,1]', 'a,b = l = __l', { '__l':[0,1] })
        test('a,l,b = 0,[1,(2,3)],4', 'a,l,b = __a, __l, __b',
             { '__a':0, '__l':[1,(2,3)], '__b':4 })
        test('a,[b,(c,d)],e = 0,(1,[2,3]),4',
             'a,[b,(c,d)],e = __a,(__b,[__c,__d]),__e',
             { '__a':0, '__b':1, '__c':2, '__d':3, '__e':4 })
        fails('a,[b,(c,d)],e = 0,[1,2],3')
        fails('a,[b,(c,d)],e = 0,[1,()],3')
        fails('a,[b,(c,d)],e = 0,[1,(2,)],3')
        fails('a,[b,(c,d)],e = 0,[1,(2,2,2)],3')

        # Complex constants
        test('a = {"a": 0, (True, False): [None, 3, "fish", ()]}', 'a = __a',
             { '__a':{'a': 0, (True, False): [None, 3, 'fish', ()]} })

        # Attributes: '.' -> '__'
        test('a.b.c    = 0', 'a.b.c    = __a__b__c', {'__a__b__c':0})
        test('a__b__c  = 0', 'a__b__c  = __a__b__c', {'__a__b__c':0}) # Bad...
        test('a_b_c    = 0', 'a_b_c    = __a_b_c',   {'__a_b_c':0})   # OK
        test('a[i].b.c = 0', 'a[i].b.c = _____b__c', {'_____b__c':0}) # Weird
        test('_.b.c    = 0', '_.b.c    = _____b__c', {'_____b__c':0}) # Bad...

        # Only extract the first occurance of a constant assignment
        test('a = 0; a = 1', 'a = __a; a = 1', { '__a':0 })
        #fixme: this test fails
#        test('a,a = 0,1', 'a,a = __a,1', { '__a':0 })
        test('if t: a = 0\na = 1', 'if t: a = __a\na = 1', { '__a':0 })
        test('a = b; a = 0; a = 1', 'a = b; a = __a; a = 1', { '__a':0 })

        # Something complex
        test('for i in l: d = f(i)\na,[b.c,b_c] = [],("foo",True)',
             'for i in l: d = f(i)\na,[b.c,b_c] = __a,(__b__c,__b_c)',
             { '__a':[], '__b__c':'foo', '__b_c':True })

        # Regression tests
        test('a,b = [0],0', 'a,b = __a,__b', { '__a':[0], '__b':0 })

class AnalysisRegressionTestCase(unittest.TestCase, NameAnalysisTestMixin):
    pass

if __name__ == '__main__':
    unittest.main(argv=sys.argv)
