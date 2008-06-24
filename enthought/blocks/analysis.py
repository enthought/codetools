import compiler, compiler.ast
from compiler.ast import (
    AssAttr, Assign, AssName, Const, Dict, Expression, Getattr, List, Name,
    Node, Tuple,
)
from compiler_.api import eval_ast
from copy import copy, deepcopy
import logging
logger = logging.getLogger(__name__)

from enthought.util.dict import map_keys, map_items
from enthought.util.functional import partial
import enthought.util.graph as graph
from enthought.util.graph import closure, topological_sort
from enthought.util.sequence import \
    all, any, disjoint, intersect, is_sequence, union
import enthought.util.tree as tree

# Extend compiler.ast.Node with a structure-preserving children query
import \
    enthought.numerical_modeling.workflow.block.compiler_.ast.get_children_tree

# XXX Hack (see #1163)
from enthought.numerical_modeling.name_magic import magically_bound_names

###############################################################################
# analysis public interface
###############################################################################

### Names #####################################################################

def free_vars(ast, *args, **kw):
    return walk(ast, NameFinder(*args, **kw)).free

def local_vars(ast, *args, **kw):
    return walk(ast, NameFinder(*args, **kw)).locals

def conditional_local_vars(ast, *args, **kw):
    return walk(ast, NameFinder(*args, **kw)).conditional_locals

### Structure #################################################################

def extract_const_assigns(ast):
    ''' Transform an AST by extracting its constant assignment statements.

        >>> from compiler import parse
        >>> from compiler_.ast.api import similar
        >>> ast, const_for = extract_const_assigns(parse('a = 0'))
        >>> similar(ast, parse('a = __a'))
        True
        >>> const_for
        {'__a': 0}
    '''
    t = ConstAssignExtractor()
    ast = t.transform(ast)
    return ast, t.const_for

def is_const(ast):
    ''' Whether an AST represents a constant expression.

        I'm not sure what "constant" means yet, but here are some examples:

            >>> from compiler import parse
            >>> all(is_const(parse(s, mode='eval')) for s in (
            ...     '0',
            ...     'True',
            ...     'None',
            ...     '"foo"',
            ...     '[1,2]',
            ...     '(False, [])',
            ...     '{"a": 1}',
            ...     '{"a": 0, (True, False): [None, 3, "fish", ()]}',
            ... ))
            True

        And some non-examples, some of which maybe should be reclassified:

            >>> any(is_const(parse(s, mode='eval')) for s in (
            ...     '0+1',
            ...     '~8',
            ...     '0 < 1',
            ...     'not True',
            ...     '"fo%s" % "o"',
            ...     'len([1,2])',
            ...     '[1,2][0]',
            ...     '[1,a]',
            ...     '[a for a in [1,2]]',
            ...     '{"a": 0}.keys()',
            ...     'set()',
            ...     'list()',
            ...     'dict()',
            ...     'dict',
            ...     'lambda: 3',
            ...     'lambda a: a',
            ... ))
            False
    '''
    return (
        isinstance(ast, Const) or
        isinstance(ast, Name) and ast.name in ['None', 'True', 'False'] or
        isinstance(ast, (List, Tuple, Dict)) and all(map(is_const, ast)) or
        isinstance(ast, Expression) and is_const(ast.node)
    )

def dependency_graph(asts, to_ast=lambda x: x):
    ''' Compute the dependency graph for a set of ASTs.

        'asts' is a sequence of either ASTs or objects 'x' such that
        'to_ast(x)' is an AST. The returned value is the dependency graph: a
        directed (acyclic) graph relating the elements of 'asts' such that a->b
        iff a's AST uses names created by b's AST. We assume 'to_ast' is
        injective and elements of 'asts' are hashable. Raises a CyclicGraph
        exception when the output graph would have been cyclic.
    
        If a name is created by multiple elements of 'asts', then the
        dependency graph won't determine a well-defined program. e.g.

            >>> from compiler import parse
            >>> assert dependency_graph(to_ast=parse, asts=[
            ...     'a = 1', 'a = 2'
            ... ]) == {
            ...     'a = 1' : [],
            ...     'a = 2' : [],
            ... }

        A topological sort of the above graph could produce either
        ['a = 1', 'a = 2'] or ['a = 2', 'a = 1'].

        Some examples:

            >>> from compiler import parse
            >>> import enthought.util.graph as graph 
            >>>
            >>> assert graph.eq(dependency_graph(to_ast=parse, asts=[
            ...     'a = b+c', 'c = 3', 'b = f(c)'
            ... ]), {
            ...     'a = b+c'  : ['c = 3', 'b = f(c)'],
            ...     'c = 3'    : [],
            ...     'b = f(c)' : ['c = 3'],
            ... })
            >>> assert graph.eq(dependency_graph(to_ast=parse, asts=[
            ...     'a = 1', 'print a', 'a = 2'
            ... ]), {
            ...     'a = 1'   : [],
            ...     'print a' : ['a = 1', 'a = 2'],
            ...     'a = 2'   : [],
            ... })
            >>> assert graph.eq(dependency_graph(to_ast=parse, asts=[
            ...     'a = 1', 'a = 0; print a', 'a = 2'
            ... ]), {
            ...     'a = 1'          : [],
            ...     'a = 0; print a' : [],
            ...     'a = 2'          : [],
            ... })

        Sorting non-linear dependency graphs is useful (but non-deterministic):

            >>> from enthought.util.graph import reverse, topological_sort
            >>>
            >>> assert topological_sort(reverse(
            ...     dependency_graph(to_ast=parse, asts=[
            ...         'c = h(a,b)',
            ...         'a = f(z)',
            ...         'b = g(z,y)',
            ...         'd = k(b,c)',
            ...     ])
            ... )) in [
            ...     [ 'a = f(z)', 'b = g(z,y)', 'c = h(a,b)', 'd = k(b,c)' ],
            ...     [ 'b = g(z,y)', 'a = f(z)', 'c = h(a,b)', 'd = k(b,c)' ],
            ... ]
    '''

    def _dependency_graph(asts):

        # Compute the dependency relation: nodes depend on their inputs, and
        # outputs depend on their nodes
        g = {}
        for ast in asts:
            v = walk(ast, NameFinder())
            g.setdefault(ast, []).extend(v.free)
            for o in v.locals | v.conditional_locals:
                g.setdefault(o, []).append(ast)

        # Take the transitive closure of the relation and return just the
        # Node-Node pairs
        g = closure(g)
        for k,vs in g.items():
            if not isinstance(k, Node):
                del g[k]
            else:
                g[k] = [ v for v in vs if isinstance(v, Node) ]
        return g

    # Push 'asts' through 'to_ast', build the graph, and then pull them back
    d = dict( (to_ast(x), x) for x in asts )
    assert len(d) == len(asts)
    return graph.map(lambda ast: d[ast], _dependency_graph(list(d)))

###############################################################################
# analysis private interface
###############################################################################

def walk(x, visitor, walker=None, verbose=None):
    "Wrap compiler.walk to handle 'None' and sequences."

    # (Nodes are iterable and strings cause infinite regress)
    if x is None:
        return visitor
    elif isinstance(x, Node):
        return compiler.walk(x, visitor, walker, verbose)
    elif is_sequence(x) and not isinstance(x, basestring):
        for n in x:
            visitor = walk(n, visitor, walker, verbose)
        return visitor
    else:
        raise ValueError(x)

class NameFinder:
    'Find and classify variable names'

    def __init__(self, free=(), locals=(), conditional_locals=(), globals=()):
        self.free = set(free)
        self.locals = set(locals)
        self.conditional_locals = set(conditional_locals)
        self.globals = set(globals)

        # Consider built-in names as global to anything
        import __builtin__
        self.globals |= set(dir(__builtin__))

        # Consider magically bound names as global to anything
        # XXX Hack (see #1163)
        self.globals |= set(magically_bound_names)

    ###########################################################################
    # NameFinder interface
    ###########################################################################

    def all_locals(self):
        return self.locals | self.conditional_locals

    def _see_unbound(self, names): # TODO I dislike this name...
        for name in set(names) - self.globals - self.locals:
            # (Conditional locals don't bind free names)

            # We need to check if the name is a dotted name.
            # If the name is a dotted name, it can be a free variable only if
            # its parent module or parent object is not already a local variable.
            prefix, suffix = '', name
            while '.' in suffix:
                if prefix == '':
                    prefix = suffix[:suffix.find('.')]
                else:
                    prefix += suffix[:suffix.find('.')]

                if prefix in self.locals:
                    return
                suffix = suffix[suffix.find('.')+1:]
                
            self.free.add(name)

    def _bind(self, names):

        # Local bindings shadow global names and replace conditional locals
        self.locals |= set(names)
        self.globals -= set(names)
        self.conditional_locals -= set(names)

        assert disjoint(self.globals, self.locals, self.conditional_locals)

    def _bind_conditional(self, names):

        # Conditional bindings shadow global names, but are precluded by
        # existing unconditional bindings
        self.conditional_locals |= set(names) - self.locals
        self.globals -= set(names)

        assert disjoint(self.globals, self.locals, self.conditional_locals)

    ###########################################################################
    # Visitor interface
    ###########################################################################

    ### Variable occurrances ##################################################

    def visitName(self, node):
        self._see_unbound([node.name])

    ### Binding occurrances ###################################################

    def visitAssName(self, node):
        if node.flags == 'OP_ASSIGN':
            self._bind([node.name])
        elif node.flags == 'OP_DELETE':
            # This is complicated. '"x" in v.conditional_locals' means, "x
            # might be bound locally, or it might be bound globally, or it
            # might be unbound." If a conditional local 'x' gets deleted, then
            # its status changes to, "x isn't bound locally, but it might be
            # bound globally, or it might be unbound." We don't have that idea
            # yet, and I'm afraid to explore its consequences... (However,
            # deleting attributes is fine because it doesn't affect name
            # analysis.)
            raise NotImplementedError("'del %s'" % node.name)
        else:
            assert False, 'Unexpected: node.flags = %r' % node.flags

    def visitAugAssign(self, node):

        # AugAssigns are things like 'a += b'. They don't use AssName, so we
        # have to handle them manually since visitAssName won't see them. (Is
        # this over-engineered? We are equating 'a += b' with 'a = a + b', but
        # should we think about it as something like 'a.add_update(b)'
        # instead?)

        # Walk the rhs normally (first)
        walk(node.expr, self)

        # Then walk the lhs. All of its names will appear free, so we have to
        # discern which are really bindings. 'a += b' binds 'a', but 'a.x += b'
        # and 'a[i] += b' don't. Augmented assign only allows Names,
        # Subscripts, and Getattrs (afaict), so we only create a new binding if
        # we have a Name lhs.
        v = walk(node.node, NameFinder())
        assert not (v.locals or v.conditional_locals)
        self._see_unbound(v.free)
        if isinstance(node.node, Name):
            self._bind(v.free)
        elif isinstance(node.node, Getattr):
            self.visitAssAttr(node.node)

    def visitGetattr(self, node):
        v = walk(node.expr, NameFinder())
        self._see_unbound([v.free.pop() + "." + node.attrname])

    def visitAssAttr(self, node):
        v = walk(node.expr, NameFinder())
        self._bind([v.free.pop() + "." + node.attrname])
        
    def visitCallFunc(self, node):
        if isinstance(node.node, Name):
            self._see_unbound([node.node.name])
        elif isinstance(node.node, Getattr):
            v = walk(node.node.expr, NameFinder())
            self._see_unbound(v.free)
        
        for arg in node.args:
            if isinstance(arg, Name):
                self._see_unbound([arg.name])
            elif isinstance(arg, Getattr):
                v = walk(arg, NameFinder())
                self._see_unbound([v.free.pop() + "." + arg.attrname])
            else:
                v = walk(arg, NameFinder())
                self._see_unbound(v.free)
                

    def visitImport(self, node):
        for name, alias in node.names:

            # If 'name' is dotted (e.g. 'os.path'), then we only introduce a
            # binding for the first name in the dotted chain (i.e. 'os'). (If
            # 'name' isn't dotted, then 'name.split(".") == [name]'.)
            name = name.split('.')[0]

            self._bind([alias or name])

    def visitFrom(self, node):
        if node.names[0][0] != '*':
            for name, alias in node.names:
                self._bind([alias or name])

    def visitGlobal(self, node):
        raise NotImplementedError(
            "'global' is useless until we allow nested scopes")

    ### Conditional binding occurrances #######################################

    def visitIf(self, node):

        unzip = lambda l: map(list, zip(*l))

        # Gather children
        tests, bodies = unzip(node.tests)
        bodies.append(node.else_)

        # Visit children
        tests_v = walk(tests, NameFinder())
        body_vs = [ walk(b, NameFinder()) for b in bodies ]
        assert not (tests_v.locals or tests_v.conditional_locals)

        # Free names come from tests and bodies
        self._see_unbound(tests_v.free | union(v.free for v in body_vs))

        # Unconditional locals come from locals that appear in every body
        # including 'else'. (If we have no 'else', then its empty visitor will
        # nullify the intersection.)
        locals = intersect(v.locals for v in body_vs)

        # Conditional locals come from conditional locals plus the rest of the
        # unconditional locals
        conditional_locals = union(v.all_locals() for v in body_vs) - locals

        self._bind(locals)
        self._bind_conditional(conditional_locals)

    def visitFor(self, node):

        # Visit children
        assign_v = walk(node.assign, NameFinder())
        list_v = walk(node.list, NameFinder())
        body_v = walk(node.body, NameFinder())
        else_v = walk(node.else_, NameFinder())
        assert not (assign_v.free or assign_v.conditional_locals)
        assert not (list_v.locals or list_v.conditional_locals)

        # Free names come from 'list', 'body' and 'else', and 'assign' binds
        # names in 'body' and 'else' (but not 'list'!)
        self._see_unbound(list_v.free)
        self._see_unbound((body_v.free | else_v.free) - assign_v.locals)

        # 'for' only produces unconditional locals when the same name is
        # bound both as a loop iterator and as an unconditional local in the
        # 'else' branch. All other bindings are conditional.
        locals = assign_v.locals & else_v.locals
        conditional_locals = (assign_v.locals | body_v.all_locals() |
                              else_v.all_locals()) - locals

        self._bind(locals)
        self._bind_conditional(conditional_locals)

    def visitWhile(self, node):

        v = walk(node.getChildNodes(), NameFinder())

        # 'while' produces no unconditional locals
        self._see_unbound(v.free)
        self._bind_conditional(v.locals | v.conditional_locals)

    def visitTryExcept(self, node):

        # If we are code after a 'try' block, then it either succeeded or
        # handled its own exception. So either the 'try' and 'else' blocks ran,
        # or some of the 'try' and one of the handlers ran. If we treat the
        # 'try' and 'else' blocks as one, then we can say that
        # 'try'/'except'/'else' produces unconditional locals when the same
        # name is local to 'try'/'else' and every handler. All other bindings
        # are conditional.

        # Visit children
        body_v = walk([node.body, node.else_], NameFinder())
        # (A handler is (type, name, body) where 'type' and 'name' can be None)
        handler_vs = [ walk(h, NameFinder()) for h in node.handlers ]
        assert all(not v.conditional_locals for v in handler_vs)

        # Free names come from 'try', 'else', and names in 'except' that aren't
        # bound by the exception name. Since 'handlers' bundles each 'except'
        # body with its exception name, the bindings are already computed.
        self._see_unbound(body_v.free | union(v.free for v in handler_vs))

        # Unconditional locals only come from locals in both the 'try'/'else'
        # body and every 'except' body. All other locals are conditional.
        locals = body_v.locals & intersect(v.locals for v in handler_vs)
        conditional_locals = \
            (body_v.all_locals() | union(v.all_locals() for v in handler_vs)) \
                - locals

        self._bind(locals)
        self._bind_conditional(conditional_locals)

    def visitTryFinally(self, node):

        # Visit children
        body_v = walk(node.body, NameFinder())
        final_v = walk(node.final, NameFinder())

        # Free names are straightforward
        self._see_unbound(body_v.free | final_v.free)

        # Locals in 'body' are conditional, locals in 'final' are unconditional
        conditional_locals = (body_v.all_locals() | final_v.conditional_locals)
        locals = final_v.locals

        self._bind(locals)
        self._bind_conditional(conditional_locals)

    # These structures are similar:
    #
    #   ListComp(expr, quals)
    #   ListCompFor(assign, list, ifs)
    #   ListCompIf(test)
    #
    #   GenExpr(code)
    #   GenExprInner(expr, quals)
    #   GenExprFor(assign, iter, ifs)
    #   GenExprIf(test)
    #
    def visitListComp(self, node):
        self._visitListCompGenExpr(node)
    def visitGenExpr(self, node):
        self._visitListCompGenExpr(node.code)
    def _visitListCompGenExpr(self, node):

        def seq(node):
            try:
                return node.list
            except AttributeError:
                return node.iter

        # Bindings scope over everything that's not a sequence, and they scope
        # over sequences to the right of their own (not including their own!).
        # All locals are conditional.

        # Visit children
        node = [ (seq(n), n.assign, n.ifs) for n in node.quals ] + [node.expr]
        v = walk(node, NameFinder())
        assert not v.conditional_locals

        self._see_unbound(v.free)
        self._bind_conditional(v.locals)

    #def visitWith(self, node) # TODO (2.5)

    ### Nested expressions that introduce bindings ############################

    def visitLambda(self, node):

        # Find free vars nearby
        walk(node.defaults, self)

        # Find free vars in lambda body (which should introduce no new
        # bindings)
        g = self.globals - set(node.argnames)
        l = self.locals | set(node.argnames)
        c = self.conditional_locals
        v = walk(node.code,
                 NameFinder(globals=g, locals=l, conditional_locals=c))
        assert v.globals == g
        assert v.locals == l
        assert v.conditional_locals == c
        self._see_unbound(v.free)

    # (Defined above)
    #def visitListComp(self, node)
    #def visitGenExpr(self, node)

    ### Specialize traversal order ############################################

    def visitAssign(self, node):

        # Walk 'expr' before 'nodes' so that lhs bindings don't capture rhs
        # free vars
        walk([node.expr] + node.nodes, self)
        
    # (Defined above)
    #def visitFor(self, node)

    ### Nested blocks #########################################################
    
    def visitKeyword(self, node):
        # kwargs are not supported due to difficulty in managing these in the graph
        logger.warn("Keyword arguments may not be correctly identified in call graph for \"%s\"" \
                    % node.name )

    def visitFunction(self, node):
        # varargs are not supported due to difficulty in managing these in the graph
        if node.varargs == 1:
            raise TypeError("varargs not supported")

        # kwargs are not supported due to difficulty in managing these in the graph
        if node.kwargs == 1:
            raise TypeError("keyword args not supported")
        
        # Find free vars nearby
        walk(node.defaults, self)

        globals      = self.globals - set(node.argnames)
        locals       = self.locals | set(node.argnames)
        conditionals = self.conditional_locals
        
        self._bind([node.name])
        
        # fixme: the inputs/outputs of functions are not set. This may cause graph errors
        #v = walk(node.code,
        #         NameFinder(globals=globals, locals=locals, conditional_locals=conditionals))
        #self._see_unbound(node.argnames)
        #self._bind(v.locals - set(node.argnames))

    # Nothing needs nested blocks yet, so we punt because the global/local
    # scoping rules are complicated. (A partially correct implementation lives
    # in the source control history (with tests!).)
    def visitClass(self, node):
        raise NotImplementedError('Nested block: %s' % node.name)
    
# A variation on the compiler module's visitor pattern
class Transformer(object):
    r'''...

        >>> from compiler import parse
        >>> from compiler_.ast.api import similar
        >>> ast = parse('if t == u: a,b = [1]+[2]\nreturn sum(b,a)')
        >>> similar(ast, Transformer().transform(ast))
        True
        >>> id(ast) == id(Transformer().transform(ast))
        False

        Transforming produces a deep copy of the input AST.
    '''

    def transform(self, x):
        if isinstance(x, Node):
            method = 'transform' + x.__class__.__name__
            if hasattr(self, method):
                return getattr(self, method)(x)
            else:
                return self._transform_children(x)
        elif is_sequence(x) and not isinstance(x, basestring):
            return x.__class__(map(self.transform, x))
        else:
            return deepcopy(x)

    def _transform_children(self, node):
        if not isinstance(node, Node):
            raise ValueError('Expected a Node, got %r' % node)

        # In these trees, strings and Nodes are leaves
        leaves = (str, Node)
        tree_map = partial(tree.tree_map, leaves=leaves)

        children = tree_map(partial(self.transform), node.getChildrenTree())
        return node.__class__(*children)

class ConstAssignExtractor(Transformer):

    def __init__(self):
        super(ConstAssignExtractor, self).__init__()
        self.const_for = {}

    def transformAssign(self, node):

        # Only transform constant assignments
        if not is_const(node.expr):
            return self._transform_children(node)

        # '__foo' names come from each lhs name at the head of the assignment:
        #   'l = a,b = 0,1' -> 'l = a,b = __a,__b', { '__a':0, '__b':1 }
        #
        # Unpack the rhs enough to map each '__foo' name to a value.
        #   'a,l = 0,[1,2]' -> 'a,l = __a,__l', { '__a':0, '__l':[1,2] }
        #   'a,l = 2'       -> SyntaxError

        def lvalue_name(node):
            'Construct a "magic" name to represent an l-value.'
            prefix = sep = '__'
            dot = '_'
            if isinstance(node, AssName):
                return prefix + node.name
            elif isinstance(node, AssAttr):
                name = node.attrname
                expr = node.expr
                while isinstance(expr, Getattr):
                    name = sep.join([expr.attrname, name])
                    expr = expr.expr
                if isinstance(expr, Name):
                    expr_name = expr.name
                else:
                    expr_name = dot
                return prefix + sep.join([expr_name, name])

        # In these trees, strings and tuples are leaves
        leaves = (str, tuple, AssAttr, AssName)
        tree_zip = partial(tree.tree_zip, leaves=leaves)
        flatten = partial(tree.flatten, leaves=leaves)
        tree_embeds = partial(tree.tree_embeds, leaves=leaves)

        # Grab the (right-most) lhs and the rhs
        lhs, rhs = node.nodes[-1], node.expr

        # Associate constants with l-value names
        if not tree_embeds(lhs, rhs):
            raise SyntaxError('Not enough r-values to unpack: %s' % node)
        zipped = flatten(tree_zip(lhs, rhs))
        const_ast_for = map_keys(lambda v: lvalue_name(v), dict(zipped))

        # Gather name<->const mappings for names we haven't seen before
        name_for = {}
        for name in const_ast_for.keys():
            if name not in self.const_for.keys():
                self.const_for[name] = eval_ast(Expression(const_ast_for[name]))
                assert const_ast_for[name] not in name_for
                name_for[const_ast_for[name]] = name

        class C(Transformer):
            def transform(self, node):
                if isinstance(node, Node) and node in name_for.keys():
                    return Name(name_for[node])
                else:
                    return super(C, self).transform(node)
        return Assign(node.nodes, C().transform(rhs))
