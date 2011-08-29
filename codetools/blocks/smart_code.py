'''
Created on Aug 2, 2011

@author: sean
'''
from __future__ import print_function

from StringIO import StringIO
from asttools import lhs, make_graph, python_source
from asttools.mutators.prune_mutator import PruneVisitor
from copy import deepcopy
from networkx.algorithms.traversal.breadth_first_search import bfs_edges
from os.path import exists
import ast as pyast
import tempfile

cmparable_code_attrs = ['co_argcount',
 'co_cellvars',
 'co_code',
 'co_consts',
 'co_flags',
 'co_freevars',
 'co_names',
 'co_nlocals',
 'co_stacksize',
 'co_varnames']

class SmartCode(object):
    '''
    A block of code that can be inspected, manipulated, and executed.
    
    The inputs requred are either:
        
    :param source: The source code as a string that the ast can be created from
    :param file: The file to read the source from.
    :param ast: The ast to compile into code. 
    :param path: the path where the source code can be found
    :param global_symbols: do not include these symbols in code graph 
    :param call_deps: if true create a cyclic depenency between caller and 
                      arguments for all function calls. 
      
    
    example::

        scode = SmartCode('a = 1; b = a + 2; c = 3')
        
        eval(scode.code)
        
        print a, b, c
        
        sub_scode = scode.restrict(inputs=['c'])
        
        print sub_scode.codestring
          
    Will produce the output::
    
        1 3 3
        
        c = 3
        
    '''

    def __init__(self, source=None, file=None, ast=None, path=None, global_symbols=None, call_deps=False):

        if global_symbols is None:
            global_symbols = set(['__builtins__'])

        if '__builtins__' in global_symbols:
            if isinstance(__builtins__, dict):
                global_symbols |= set(__builtins__)
            else:
                global_symbols |= set(dir(__builtins__))

        if ast is None:
            if not ((source is None) ^ (file is None)):
                raise TypeError("only one of the arguments source or file may be specified")

            if source is not None:
                self.source = source
                if path is  None:
                    path = tempfile.mktemp('.py')
                elif exists(path):
                    raise TypeError('path should not exist if argument source is given')
                self.path = path

                try:
                    with open(self.path, 'w') as fd:
                        fd.write(self.source)
                except IOError:
                    pass

            else: # file is not None
                self.path = file.name
                self.source = file.read()

            self.ast = pyast.parse(self.source, self.path, 'exec')
        else: # ast is not None
            self.source = source
            self.path = path
            self.ast = ast

        self.code = compile(self.ast, self.path, 'exec', dont_inherit=True)

        self._graph, self._undefined = make_graph(self.ast, call_deps=call_deps)

        self.global_symbols = (set(self._graph.nodes()) & set(global_symbols)) - lhs(self.ast)

        for symbol in self.global_symbols:
            self._graph.remove_node(symbol)

    @property
    def nodes(self):
        ''':return: A list of all symbols seen in the code.
        '''
        return set(self._graph.nodes())

    @property
    def undefined(self):
        ''':return: A list of all undefined symbols
        '''
        return self._undefined - self.global_symbols

    def __repr__(self):
        from os.path import split
        return '<%s codehash=%r file=%r>' % (type(self).__name__, hash(self.code), split(self.path)[-1])

    def __getstate__(self):
        self_dict = self.__dict__.copy()
        self_dict.pop('code')
        return self_dict

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.code = compile(self.ast, self.path, 'exec')

    def __hash__(self):
        return hash(self.code)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return all([(getattr(self.code, attr) == getattr(other.code, attr)) for attr in cmparable_code_attrs])

    def __ne__(self, other):
        if not isinstance(other, type(self)):
            return True
        return any([(getattr(self.code, attr) != getattr(other.code, attr)) for attr in cmparable_code_attrs])

    @property
    def variables(self):
        'all local symbols found in the ast'
        return self.nodes - self.global_symbols

    def lines(self):
        '''
        Split a block into smallest atomic statements.
    
        :param block: the block to split into sub - blocks
        :param reversed: The generator will yield the blocks in reverse order
        '''

        if len(self.ast.body) <= 1:
            yield self
            return

        body = deepcopy(self.ast.body)

        for stmnt in body:
            mod = pyast.Module(body=[stmnt])

            sub_code = SmartCode(ast=mod, path=self.path, global_symbols=self.global_symbols)
            yield sub_code

    @property
    def codestring(self):
        '''
        Return the source-code generated from the ast. 
        '''
        file = StringIO()
        python_source(self.ast, file)
        file.seek(0)
        return file.read()

    def depends_on(self, inputs=()):
        '''
        Get the dependencies for a set of inputs
        
        Traverse the graph in reverse order to find the symbols that can be produced by each input in inputs. 

        :param inputs:         
        '''
        g = self._graph
        gr = g.reverse()

        inputs = set(inputs)

        if not inputs.issubset(self.variables):
            raise ValueError('Unknown rhs: %s' % (inputs - self.variables))

        nodes = set(inputs)

        for input in inputs:
            edgelist = bfs_edges(gr, source=input)
            nodelist = [node for edge in edgelist for node in edge]
            nodes.update(nodelist)

        return nodes

    def dependent_on(self, outputs=()):
        '''
        Get the dependencies for a set of inputs and a set of outputs.
        
        Traverse the graph to find the required symbols to produces each output in outputs.
         
        Traverse the graph in reverse order to find the symbols that can be produced by each input in inputs. 

        :param inputs: 
        :param outputs:
        
        '''
        g = self._graph

        outputs = set(outputs)

        if not outputs.issubset(self.variables):
            raise ValueError('Unknown lhs: %s' % (outputs - self.variables))

        nodes = set(outputs)

        for output in outputs:
            edgelist = bfs_edges(g, source=output)
            nodelist = [node for edge in edgelist for node in edge]
            nodes.update(nodelist)

        return nodes

    def restrict(self, inputs=(), outputs=()):
        ''' The minimal sub-block that computes 'outputs' from 'inputs'.

            Consider the block:

                x = expensive()
                x = 2
                y = f(x, a)
                z = g(x, a)
                w = h(a)

            This block has inputs 'a' (and 'f', 'g', 'h', and 'expensive'), and
            outputs 'x', 'y', 'z', and 'w'. If one is only interested in
            computing 'z', then lines 1, 3, and 5 can be omitted. Similarly, if
            one is only interested in propagating the effects of changing 'a',
            then lines 1 and 2 can be omitted. And if one only wants to
            recompute 'z' after changing 'a', then all but line 4 can be
            omitted.

            In this fashion, 'restrict' computes the minimal sub-block that
            computes 'outputs' from 'inputs'. See the tests in
            'block_test_case.BlockRestrictionTestCase' for concrete examples.

            Assumes 'inputs' and 'outputs' are subsets of 'self.inputs' and
            'self.outputs', respectively.
        '''

        if not (inputs or outputs):
            raise ValueError('Must provide inputs or outputs')

        ast = deepcopy(self.ast)

        #===============================================================================
        # Remove any staement that does not contain an input anywhere in
        # the expression
        #===============================================================================
        if inputs:
            to_remove = self.variables - self.depends_on(inputs)
            gen = PruneVisitor(to_remove, mode='exclusive')
            gen.visit(ast)

        #===============================================================================
        # Remove any staement that does not contain an input anywhere in
        # the expression
        #===============================================================================
        if outputs:
            to_remove = self.variables - self.dependent_on(outputs)
            gen = PruneVisitor(to_remove, mode='inclusive')
            gen.visit(ast)

        return SmartCode(ast=ast, path=self.path, source=self.source, global_symbols=self.global_symbols)



