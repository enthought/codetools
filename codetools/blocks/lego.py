'''
Created on Aug 5, 2011

@author: sean
'''
from meta.asttools.mutators.remove_trivial import \
    remove_trivial as remove_trivial_ast
from meta.asttools import lhs, rhs, dump_python_source
from codetools.blocks.smart_code import SmartCode
from copy import deepcopy
#from pygraph.algorithms.cycles import find_cycle #@UnresolvedImport
#from pygraph.algorithms.sorting import \
#    topological_sorting as topo_sort #@UnresolvedImport
#from pygraph.classes.digraph import digraph #@UnresolvedImport

from networkx import DiGraph
from networkx import topological_sort as topo_sort
from networkx.algorithms.cycles import simple_cycles
import _ast
import traceback
from codetools.util.cbook import flatten


class DependencyCycleError(Exception):
    def __init__(self, nodes):
        self.nodes = nodes
        nodestrs = []
        for l, r in nodes:
            ns = '%s = %s' % (', '.join(l), ' : '.join(r))
            nodestrs.append(ns)
        Exception.__init__(self, ' -> '.join(nodestrs))


leaves = lambda graph: [node for node in graph.nodes() if not graph.neighbors(node)]

def split_contant_values(scode):
    '''
    Split scode into to SmartCode objects the first containing all of the constant assignments. 
    The second will contain the rest of the code.
    
    example::
        
        >>> scode = SmartCode('import math; a = 1; b = a + 1')
        >>> const, variable = split_contant_values(scode)
        >>> print const.codestring
        import math
        a = 1 
        >>> print variable.codestring
        b = a + 1

    '''
    constant_symbols = leaves(scode._graph)

    if not constant_symbols:
        return SmartCode(''), scode

    r_graph = scode._graph.reverse()
    new_inputs = set.union(*[set(r_graph.neighbors(node)) for node in constant_symbols])

    if not new_inputs:
        return scode, SmartCode('')

    const_scode = scode.restrict(outputs=constant_symbols)
    var_scode = scode.restrict(inputs=new_inputs)

    return const_scode, var_scode

def split(scode, reversed=True):
    '''
    Split a scode into smallest *sortable* atomic statements.

    :param scode: the scode to split into sub - scodes
    :param reversed: The generator will yield the scodes in reverse order
    
    
    :return: a list of scodes
    
    
    sco
    
    '''

    if reversed:
        shift = lambda left, right:  left.insert(0, right.pop())
    else:
        shift = lambda left, right:  left.append(right.pop(0))

    if len(scode.ast.body) <= 1:
        yield scode

    body = deepcopy(scode.ast.body)

    while body:
        blob = []
        shift(blob, body)

        while lhs(blob).intersection(lhs(body)):
            shift(blob, body)

        mod = _ast.Module(body=blob)

        sub_scode = SmartCode(ast=mod, path=scode.path)
        yield sub_scode

def join(scodes):
    '''
    Join a sequence of scodes into a single Block containing
    single ast and code objects.

    :param scodes: a sequence of scodes to join
    '''
    body = []
    mod = _ast.Module(body=body)
    for scode in scodes:
        sub_body = deepcopy(scode.ast.body)
        for i in range(len(sub_body)):
            if isinstance(sub_body[i], _ast.Pass):
                del sub_body[i]
        body.extend(sub_body)

    return SmartCode(source=dump_python_source(mod))

def sort(scodes):
    '''
    Build a graph from the scodes and topologically sort it.

    The dependencies on the graph are based on symbols returned
    from the lhs and rhs functions.

    :param scodes: Block objects to sort.
    '''

    graph = DiGraph()

    for scode in scodes:
        graph.add_node(scode)

    input_dict = {}
    output_dict = {}

    for scode in scodes:
        for intput in rhs(scode.ast):
            input_dict.setdefault(intput, []).append(scode)
        for output in lhs(scode.ast):
            output_dict.setdefault(output, []).append(scode)

    for var in set(input_dict) | set(output_dict):
        for iscode in input_dict.get(var, []):
            for oscode in output_dict.get(var, []):

                edge = oscode, iscode
                graph.add_edge(*edge)

    cycles = simple_cycles(graph)
    if len(cycles):
        raise DependencyCycleError([(lhs(b.ast), rhs(b.ast)) for b in cycles[0]])
    return topo_sort(graph)

def interleave(scodes):
    '''
    Sort and join scodes.

    :param scodes: sequence of Block objects
    
    
    :return: a SmartCode object
    
    example::
     
        scode1 = SmartCode('a = 1; c = a + b')
        scode2 = SmartCode('b = a ** 2')
        
        scode = interleave([scode1, scode2])
        
        print scode.codestring
        
    results in ::
    
        a = 1
        b = (a ** 2)
        c = (a + b)

    '''

    return join(sort(flatten([split(scode) for scode in scodes])))


def remove_trivial(scode):
    '''
    Remove duplicate assignments and other
    trivial optimizations.

    :param scode: Block object

    :returns: a new scode object
    '''

    new_ast = deepcopy(scode.ast)
    remove_trivial_ast(new_ast)
    return SmartCode(ast=new_ast, path=scode.path)

def eval_inline(codes, global_context=None, local_context=None, continue_on_errors=False):

    globals = global_context if global_context is not None else {}
    local_context = local_context if local_context is not None else {}

    for code in codes:
        try:
            eval(code, globals, local_context)
        except Exception as err:
            if continue_on_errors:
                traceback.print_exc()
            else:
                raise err

def unique_lhs(scodes):
    '''
    Return a dict whose values are from `scodes` and who's keys are
    hashed based on the lhs symbols of assignment statements.
     
    :param scodes: sequence of Block objects
    '''

    def o(b):
        result = tuple(sorted(lhs(b.ast)))
        if result:
            return result
        else:
            return b.code

    return {o(b):b for b in scodes}

