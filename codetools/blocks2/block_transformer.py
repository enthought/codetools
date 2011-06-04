import ast
from ast import Module, NodeTransformer
import token

class BlockTransformer(NodeTransformer, object):
    """Specialize how code parses into ASTs for Blocks."""

    ###########################################################################
    # BlockTransformer protected interface
    ###########################################################################

    # What we rewrite 'from %s import *' into
    _rewrite_wildcard_into = ("import %s as __module\n"
                              "for name in dir(__module):\n"
                              "    exec '%%s = __module.%%s' %% (name, name)\n"
                              "del __module\n")

    ###########################################################################
    # Transformer public interface
    ###########################################################################

    def visit_ImportFrom(self, nodelist):
        r'''Translate 'from ... import \*' statements into 'import ...'.

            We avoid 'from ... import \*' because they only seem to work on
            built-in dicts, whereas we run code over user dicts. Our solution
            is to translate them into normal import statements::

                from foo import *
                ~>
                import foo as __module
                for name in dir(__module):
                    exec '%s = __module.%s' % (name, name)

            This translation is equivalent except it leaves the name '__module'
            in the namespace.

            This implementation assumes that the compiler equates nested 'Stmt'
            nodes with flat ones, e.g.:

            >>> from compiler.ast import Assign, AssName, Const, Stmt
            >>> from codetools.blocks.compiler_.api\
            ...     import compile_ast
            >>>
            >>> def ass(**kw):
            ...     [(name, n)] = kw.items()
            ...     return Assign([AssName(name, 'OP_ASSIGN')], Const(n))
            >>>
            >>> s1 = Stmt([ass(a=1), ass(b=2), ass(c=3)])
            >>> s2 = Stmt([ass(a=1), Stmt([ass(b=2)]), ass(c=3)])
            >>>
            >>> assert compile_ast(Module(None, s1)) == \
            ...        compile_ast(Module(None, s2))
        '''

        if nodelist[3][0] == token.STAR:

            ast = self.parsesuite(self._rewrite_wildcard_into %
                                  self.com_dotted_name(nodelist[1]))

            # Puts 'Stmt([Import(...), For(...)])' where 'From(...)' would have
            # gone. (See assumption above.)
            assert isinstance(ast, Module)
            return ast.node

        else:
            return super(BlockTransformer, self).visit_ImportFrom(nodelist)
