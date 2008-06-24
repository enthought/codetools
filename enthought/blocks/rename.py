""" Remanes tokens in compiler.ast structures.

"""

import sys
import cStringIO
from compiler.ast import Const, Name, Tuple

def rename(ast, mode, old, new):
    if mode not in ['variable', 'function']:
        raise ValueError("mode '%s' not supported")
    
    rename_ast = RenameAst(ast, mode, old, new)
    
    return rename_ast.tree, rename_ast.modifications

class RenameAst:
    """ Methods in this class recursively traverse an AST and
        rename tokens
    """

    #########################################################################
    # object interface.
    #########################################################################

    def __init__(self, tree, mode, old, new):
        """ Unparser(tree, mode, old, new) -> None.

            For a given mode, renames all occurences of old to new.
            'variable' and 'function' are the only modes currently supported
        """
        self.mode = mode
        self.old = old
        self.new = new
        self.tree = tree
        self.modifications = 0
        
        self._dispatch(self.tree)

    #########################################################################
    # RenameAst private interface.
    #########################################################################

    ### format, output, and dispatch methods ################################

    def _dispatch(self, tree):
        "_dispatcher function, _dispatching tree type T to method _T."
        if isinstance(tree, list):
            for t in tree:
                result.append(self._dispatch(t))
            return
        
        if tree.__class__.__name__ == 'NoneType' and not self._do_indent:
            return
        
        if tree.__class__.__name__ == 'NoneType' and not self._do_indent:
            return
        
        if hasattr(self, "_"+tree.__class__.__name__):
            meth = getattr(self, "_"+tree.__class__.__name__)
            meth(tree)


    #########################################################################
    # compiler.ast unparsing methods.
    #
    # There should be one method per concrete grammar type. They are
    # organized in alphabetical order.
    #########################################################################

    def _Add(self, t):
        self._dispatch(t.left)
        self._dispatch(t.right)

    def _And(self, t):
        for node in t.nodes:
            self._dispatch(node)
                
#    def _AssAttr(self, t):
#        """ Handle assigning an attribute of an object
#        """
#        self._dispatch(t.expr)
 
    def _Assign(self, t):
        """ Expression Assignment such as "a = 1".

            This only handles assignment in expressions.  Keyword assignment
            is handled separately.
        """
        for node in t.nodes:
            self._dispatch(node)
        
        self._dispatch(t.expr)

    def _AssName(self, t):
        """ Name on left hand side of expression.

            Treat just like a name on the right side of an expression.
        """
        if t.name == self.old:
            t.name = self.new
            self.modifications += 1

    def _AssTuple(self, t):
        """ Tuple on left hand side of an expression.
        """
        for node in t.nodes:
            self._dispatch(node)

    def _AugAssign(self, t):
        """ +=,-=,*=,/=,**=, etc. operations
        """
        self._dispatch(t.node)
        self._dispatch(t.expr)
            
    def _Bitand(self, t):
        """ Bit and operation.
        """        
        for node in t.nodes:
            self._dispatch(node)
                
    def _Bitor(self, t):
        """ Bit or operation
        """
        for node in t.nodes:
            self._dispatch(node)
                
    def _CallFunc(self, t):
        """ Function call.
        """
        if self.mode == "function":
            self._dispatch(t.node)
            
        for arg in t.args:
            self._dispatch(arg)        

    def _Compare(self, t):
        """ Comparison operator.
        """
        self._dispatch(t.expr)
        
        for op in t.ops:
            self._dispatch(op[1])

#    def _Decorators(self, t):
#        """ Handle function decorators (eg. @has_units)
#        """
#        for node in t.nodes:
#            self._dispatch(node)

    def _Dict(self, t):
        """ Dictionary declaration
        """
        for item in t.items:
            self._dispatch(item[0])
            self._dispatch(item[1])

    def _Discard(self, t):
        """ Node for when return value is ignored such as in "foo(a)".
        """
        self._dispatch(t.expr)

    def _Div(self, t):
        self.__binary_op(t, '/')

    def _FloorDiv(self, t):
        self.__binary_op(t, '/')
        
    def _For(self, t):
        self._dispatch(t.assign)
        self._dispatch(t.list)
        self._dispatch(t.body)
        if t.else_ is not None:
            self._dispatch(t.else_)

#    def _From(self, t):
#        """ Handle "from xyz import foo, bar as baz".
#        """
#        self._dispatch(t.modname)
#        self._Import(t)        
                
    def _Function(self, t):
        """ Handle function definitions
        """
        if t.decorators is not None:
            self._dispatch(t.decorators)
            
        if self.mode == 'function' and t.name == self.old:
            t.name = self.new
            self.modifications += 1
        
        for i, name in enumerate(t.argnames):
            if self.mode == 'variable' and name == self.old:
                t.argnames[i] = self.new
                self.modifications += 1
                
        self._dispatch(t.code)

    def _Getattr(self, t):
        """ Handle getting an attribute of an object
        
            fixme: decide what to do about hierarchical names
        """
        self._dispatch(t.expr)
                
    def _If(self, t):
        for test in t.tests:
            self._dispatch(test[0])
            self._dispatch(test[1])
            
        if t.else_ is not None:
            self._dispatch(t.else_)
            
#    def _Import(self, t):
#        for i, name in enumerate(t.names):
#            if self.mode == 'function' and name[0] == self.old:
#                l = list(name[0])
#                l[0] = self.new
#                t.names[i] = tuple(l)
#                self.modifications += 1

    def _Keyword(self, t):
        """ Keyword value assignment within function calls and definitions.
        """
        if self.mode == 'variable' and t.name == self.old:
            t.name = self.new
            self.modifications += 1
            
        self._dispatch(t.expr)

    def Lambda(self, t):
        for i, name in enumerate(t.argnames):
            if self.mode == 'variable' and name == self.old:
                t.argnames[i] = self.new
                self.modifications += 1
                
        self._dispatch(t.code)

    def _LeftShift(self):
        self.__binary_op(t, '<<')

    def _List(self, t):
        for node in t.nodes:
            self._dispatch(node)
            
    def _ListComp(self, t):
        self._dispatch(t.expr)
        
        for qual in t.quals:
            self._dispatch(qual)
            
    def _ListCompFor(self, t):
        self._dispatch(t.assign)
        self._dispatch(t.list)
        
        for if_ in t.ifs:
            self._dispatch(if_)
            
    def _ListCompIf(self, t):
        self._dispatch(t.test)
        
    def _Module(self, t):
        self._dispatch(t.node)

    def _Mul(self, t):
        self.__binary_op(t, '*')

    def _Name(self, t):
        if self.old == t.name:
            t.name = self.new
            self.modifications += 1
        
    def _Or(self, t):
        for node in t.nodes:
            self._dispatch(node)
                
    def _Print(self, t):
        for node in t.nodes:
            self._dispatch(node)
    
    def _Printnl(self, t):
        self._Print(t)

    def _Power(self, t):
        self.__binary_op(t, '**')

    def _Raise(self, t):
        self._dispatch(t.expr1)
        self._dispatch(t.expr2)
        self._dispatch(t.expr3)

    def _Return(self, t):
        self._dispatch(t.value)

    def _Slice(self, t):
        self._dispatch(t.expr)
        self._dispatch(t.lower)
        self._dispatch(t.upper)

    def _Sliceobj(self, t):
        for node in t.nodes:
            self._dispatch(node)

    def _Stmt(self, t):
        for node in t.nodes:
            self._dispatch(node)

    def _Sub(self, t):
        self.__binary_op(t, '-')

    def _Subscript(self, t):
        self._dispatch(t.expr)
        
        for sub in t.subs:
            self._dispatch(sub)
            
    def _TryExcept(self, t):
        self._dispatch(t.body)
        
        for handler in t.handlers:
            self._dispatch(handler[0])
            self._dispatch(handler[1])
            
        if t.else_ is not None:
            self._dispatch(t.else_)

    def _Tuple(self, t):
        for node in t.nodes:
            self._dispatch(node)
            
    def _UnaryAdd(self, t):
        self._write("+")
        self._dispatch(t.expr)
        
    def _UnarySub(self, t):
        self._write("-")
        self._dispatch(t.expr)        

    def _With(self, t):
        self._dispatch(t.expr)
        self._dispatch(t.body)
        
        if t.vars is not None:
            self._dispatch(t.vars)
        
    def __binary_op(self, t, symbol):
        self._dispatch(t.left)
        self._dispatch(t.right)
        
        
if __name__ == "__main__":
    from block import Block
    code = "with m as z:\n"\
           "   if(a<3): print foo(1)\n"\
           "   else: print foo(2)"
           
    bl = Block(code)
    ast = bl.ast
    print rename(ast, 'variable', 'a', 'A')
    print rename(ast, 'variable', 'm', 'M')
    print rename(ast, 'variable', 'foo', 'FOO')
    print rename(ast, 'function', 'foo', 'Foo')
    