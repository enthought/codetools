'''
Created on Aug 5, 2011

@author: sean
'''
from asttools.mutators.remove_trivial import \
    remove_trivial as remove_trivial_ast
from asttools.visitors.assign_visitor import lhs, rhs
from asttools.visitors.pysourcegen import dump_python_source
from codetools.blocks.smart_code import SmartCode
from copy import deepcopy
from pygraph.algorithms.cycles import find_cycle #@UnresolvedImport
from pygraph.algorithms.sorting import \
    topological_sorting as topo_sort #@UnresolvedImport
from pygraph.classes.digraph import digraph #@UnresolvedImport
import _ast
import traceback


class DependencyCycleError(Exception):
    def __init__(self, nodes):
        self.nodes = nodes
        nodestrs = []
        for l, r in nodes:
            ns = '%s = %s' % (', '.join(l), ' : '.join(r))
            nodestrs.append(ns)
        Exception.__init__(self, ' -> '.join(nodestrs))


def split(block, reversed=True):
    '''
    Split a block into smallest atomic statements.

    :param block: the block to split into sub - blocks
    :param reversed: The generator will yield the blocks in reverse order
    '''

    if reversed:
        shift = lambda left, right:  left.insert(0, right.pop())
    else:
        shift = lambda left, right:  left.append(right.pop(0))

    if len(block.ast.body) <= 1:
        yield block

    body = deepcopy(block.ast.body)

    while body:
        blob = []
        shift(blob, body)

        while lhs(blob).intersection(lhs(body)):
            shift(blob, body)

        mod = _ast.Module(body=blob)

        sub_block = SmartCode(ast=mod, path=block.path)
        yield sub_block

def join(blocks):
    '''
    Join a sequence of blocks into a single Block containing
    single ast and code objects.

    :param blocks: a sequence of blocks to join
    '''
    body = []
    mod = _ast.Module(body=body)
    for block in blocks:
        sub_body = deepcopy(block.ast.body)
        for i in range(len(sub_body)):
            if isinstance(sub_body[i], _ast.Pass):
                del sub_body[i]
        body.extend(sub_body)

    return SmartCode(source=dump_python_source(mod))

def sort(blocks):
    '''
    Build a graph from the blocks and topologically sort it.

    The dependencies on the graph are based on symbols returned
    from the lhs and rhs functions.

    :param blocks: Block objects to sort.
    '''

    graph = digraph()

    graph.add_nodes(blocks)

    input_dict = {}
    output_dict = {}

    for block in blocks:
        for intput in rhs(block.ast):
            input_dict.setdefault(intput, []).append(block)
        for output in lhs(block.ast):
            output_dict.setdefault(output, []).append(block)

    for var in set(input_dict) | set(output_dict):
        for iblock in input_dict.get(var, []):
            for oblock in output_dict.get(var, []):

                edge = oblock, iblock
                graph.add_edge(edge)

    cycle = find_cycle(graph)
    if cycle:
        raise DependencyCycleError([(lhs(b.ast), rhs(b.ast)) for b in cycle])
    return topo_sort(graph)

def interleave(blocks):
    '''
    Sort and join blocks.

    :param blocks: sequence of Block objects

    '''
    return join(sort(blocks))


def remove_trivial(block):
    '''
    Remove duplicate assignments and other
    trivial optimizations.

    :param block: Block object

    :returns: a new block object
    '''

    new_ast = deepcopy(block.ast)
    remove_trivial_ast(new_ast)
    return SmartCode(ast=new_ast, path=block.path)

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

def unique_lhs(blocks):
    '''
    Return a dict whose values are from `blocks` and who's keys are
    hashed based on the lhs symbols of assignment statements.
     
    :param blocks: sequence of Block objects
    '''

    def o(b):
        result = tuple(sorted(lhs(b.ast)))
        if result:
            return result
        else:
            return b.code

    return {o(b):b for b in blocks}

