"""Simple blocks of python code with dependency analysis.

Updated to use Python's new version of the Abstract Syntax Tree
from the old compiler.ast module.  -Anthony Scopatz
"""

from __future__ import print_function

import ast
#from ast import mod, stmt, expr, expr_context, slice, boolop, operator, \
#    unaryop, cmpop, comprehension, excepthandler, arguments, keyword, alias
from ast import AST, Module, stmt

from traceback import format_exc
import types
from uuid import UUID, uuid4

from six import exec_

from traits.api import (Bool, Dict, Either, HasTraits,
                                  Instance, List, Property, Str,
                                  cached_property, Event)

from ..util.dict import map_keys, map_values
from ..util import graph
from ..util.sequence import is_sequence

from .analysis import NameFinder

from .block_transformer import BlockTransformer
from codetools.blocks.compiler_unparse import unparse

###############################################################################
# TODO:
#  - Blocks should listen to changes in each sub-block
#  - Unify 'Block' and 'Expression'
#  - Should we be copying AST objects...?
#  - Decompose more than just Stmt's
#  - Expose functions that blocks use? (e.g. simply by name)
###############################################################################

class CompositeException(Exception):
    """A container to consolidate multiple exceptions"""
    def __init__(self, exceptions):
        self.exceptions = exceptions

class ShadowDict(dict):
    """ Dictionary whose writes (via indexing) are also saved in a shadow
    dictionary.
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.shadow = {}  # only give shadow new objects, not those already in dict.

    def __setitem__(self, key, val):
        "write new objects into a shadow dict as well as the base dict"
        dict.__setitem__(self, key, val)  # avoids recursion
        self.shadow[key] = val


class Block(HasTraits):
    'A block of code that can be inspected, manipulated, and executed.'

    __this = Instance('Block') # (traits.This scopes dynamically (#986))

    ###########################################################################
    # Block traits
    ###########################################################################

    ### Public traits ########################################################

    # Input and output parameters
    inputs = Property(Instance(set))
    _inputs = Instance(set)
    outputs = Property(Instance(set))
    _outputs = Instance(set)
    conditional_outputs = Property(Instance(set))
    _conditional_outputs = Instance(set)
    all_outputs = Property(Instance(set))
    _get_all_outputs = lambda self: self.outputs | self.conditional_outputs
    const_assign = Property(Instance(tuple))
    fromimports = Property(Instance(set))
    imports_ast = Property(Instance(AST))

    # The sequence of sub-blocks that make up this block, if any. If we don't
    # decompose into sub-blocks, 'sub_blocks' is None.
    sub_blocks = List(__this)

    # The AST that represents our behavior
    # AST replaces Node
    # Aslo note that this variable name is hard to choose.
    # It was originally called 'ast', but since this is the same name as
    # the module, it needed to be changed.  Other possibilities considered
    # were: as_tree, Ast, a_s_tree, astree, a_s_t.
    ast_tree = Instance(AST)

    # The name of the file this block represents, if any. For blocks that
    # aren't files, the default value just shows repr(self). Annotates
    # tracebacks.
    filename = Instance(basestring) # (Default 'None', allow 'None')

    # A unique identifier
    uuid = Instance(UUID)
    _uuid_default = lambda self: uuid4()

    # Enabling this makes tracebacks less useful but speeds up Block.execute.
    # The problem is that a code object has a unique filename ('co_filename'),
    # so we can compile all of our sub-blocks' ASTs into a single code object
    # only if we ignore the fact that they might each come from different
    # files.
    no_filenames_in_tracebacks = Bool(False)

    # Is this block the result of merging other blocks?
    grouped = Bool(False)

    ### Protected traits #####################################################

    # The dependency graph for 'sub_blocks', if they exist. If we don't
    # decompose into sub-blocks, '_dep_graph' is None. The '_dep_graph'
    # property uses '__dep_graph' as a cache, and '__dep_graph_is_valid =
    # False' invalidates the cache. ('__dep_graph = None' is valid, so we need
    # to track validity with another variable.)
    _dep_graph = Property(Either(Dict, None))
    __dep_graph = Either(Dict, None)
    __dep_graph_is_valid = Bool(False)

    _code = Property(depends_on='_code_invalidated, ast')
    _code_invalidated = Event()


    # Flag to break call cycles when we update 'ast' and 'sub_blocks'
    _updating_structure = Bool(False)

    codestring = Property
    _stored_string = Str('')
    # A cache for block restrictions. Invalidates when structure changes.
    __restrictions = Dict

    ###########################################################################
    # object interface
    ###########################################################################

    def __init__(self, x=(), file=None, grouped=False, **kw):
        super(Block, self).__init__(**kw)

        # fixme: Why not use static handlers for this?
        self.on_trait_change(self._structure_changed, 'sub_blocks')
        self.on_trait_change(self._structure_changed, 'sub_blocks_items')
        self.on_trait_change(self._structure_changed, 'ast_tree')

        # Interpret arguments:

        is_file_object = lambda o: hasattr(o, 'read') and hasattr(o, 'name')

        # 'file' -> 'x'
        if file is not None:
            # Turn 'file' into a file object and move to 'x'
            if isinstance(file, basestring):
                file = open(file)
            elif not is_file_object(file):
                raise ValueError("Expected 'file' to be a file or string, "
                                 "got %r" % file)
            x = file

        # 'x': file object -> string
        saved_filename = None
        if is_file_object(x):
            self.filename = x.name
            saved_filename = self.filename
            x = x.read()

        # 'x' -> 'self.ast_tree' or 'self.sub_blocks'
        if isinstance(x, basestring):
            self.ast_tree = ast.parse(x, mode='exec')
            # (BlockTransformer handles things like 'import *')
            self.ast_tree = BlockTransformer().visit(self.ast_tree)
            self._stored_string = x
        elif isinstance(x, AST):
            # push an exception handler onto the stack to ensure that the calling function gets the error
            #push_exception_handler(handler = lambda o,t,ov,nv: None, reraise_exceptions=True)
            self._updating_structure = True

            self.ast_tree = x

            self._updating_structure = False
            #pop_exception_handler()
        elif is_sequence(x):
            if len(x) == 0:
                self.ast_tree = stmt([])
            sub_blocks = []
            for block in map(to_block, x):
                if block.sub_blocks is None or len(block.sub_blocks) == 0:
                    sub_blocks.append(block)
                else:
                    sub_blocks += block.sub_blocks
            self.sub_blocks = sub_blocks
        else:
            raise ValueError('Expecting file, string, AST, or sequence. Got %r' % x)

        # prepare the inputs and outputs
        self._clear_cache_inputs_and_outputs()

        # We really want to keep the filename for "pristine" blocks, and
        # _structure_changed nukes it most times
        self.filename = saved_filename

        # Set flag whether this is a grouped block or not
        self.grouped = grouped

    def __eq__(self, other):
        return type(self) == type(other) and self.uuid == other.uuid

    def __hash__(self):
        return hash((type(self), self.uuid))

    def __getstate__(self):

        # Evaluate attributes with non-deterministic default values to force
        # their initialization (see #1023)
        self.uuid

        # get the state but remove the code object cache
        state = super(Block, self).__getstate__()

        state['_Block_version'] = 1

        return state

    def __setstate__(self, state):

        version = state.pop('_Block_version', 0)

        if version < 1:
            if state.has_key('inputs'):
                 state['_inputs'] = state.pop('inputs')
            if state.has_key('outputs'):
                 state['_outputs'] = state.pop('outputs')
            if state.has_key('conditional_outputs'):
                 state['_conditional_outputs'] = state.pop('conditional_outputs')

        super(Block, self).__setstate__(state)

        # reset the dynamic trait change handlers
        # fixme: Why not use static handlers for this?
        self.on_trait_change(self._structure_changed, 'sub_blocks')
        self.on_trait_change(self._structure_changed, 'sub_blocks_items')
        self.on_trait_change(self._structure_changed, 'ast_tree')

    def __repr__(self):
        return '%s(uuid=%s)' % (self.__class__.__name__, self.uuid)

    def __str__(self):
        return repr(self) # TODO Unparse ast (2.5) (cf. #1167)

    def _print_debug_graph(self, graph):
        """ Only to be used for debugging- prints each node of the graph
            with its immediate dependents following
        """
        print("--------------------------------------")
        for k in graph.keys():
            if isinstance(k, Block):
                print(k.ast)
                for dep in graph[k]:
                    if isinstance(dep, Block):
                        print("    %s" % dep.ast)
                    else:
                        print("    '%s'" % dep[0])

    ###########################################################################
    # Block public interface
    ###########################################################################

    def remove_sub_block(self, uuid):
        if self.sub_blocks is None:
            raise KeyError()
        for sb in self.sub_blocks:
            if sb.uuid == uuid:
                self.sub_blocks.remove(sb)
                break

    def is_empty(self):
        """ Return true if 'block' has an empty AST.
        """

        return isinstance(self.ast, Stmt) and len(self.ast.nodes) == 0


    def execute(self, local_context, global_context = {}, continue_on_errors=False):
        """Execute the block in local_context, optionally specifying a global
        context.  If continue_on_errors is specified, continue executing code after
        an exception is thrown and throw the exceptions at the end of execution.
        if more than one exception was thrown, combine them in a CompositeException"""
        # To get tracebacks to show the right filename for any line in any
        # sub-block, we need each sub-block to compile its own '_code' since a
        # code object only keeps one filename. This is slow, so we give the
        # user the option 'no_filenames_in_tracebacks' to gain speed but lose
        # readability of tracebacks.


        if (len(self.sub_blocks) == 0 or self.no_filenames_in_tracebacks) and \
               not continue_on_errors:
            if self.filename:
                local_context['__file__'] = self.filename
            exec_(self._code, global_context, local_context)
        else:
            if continue_on_errors:
                exceptions = []
                for block in self.sub_blocks:
                    try:
                        block.execute(local_context, global_context)
                    except Exception as e:
                        # save the current traceback
                        e.traceback = format_exc()
                        exceptions.append(e)
                if exceptions:
                    if len(exceptions)>1:
                        raise CompositeException(exceptions)
                    else:
                        raise exceptions[0]

            else:
                for block in self.sub_blocks:
                    block.execute(local_context, global_context)
        return

    def execute_impure(self, context, continue_on_errors=False,
                       clean_shadow=True):
        """Execution of a block the does not has all of its dependecies satisfied.

        Summary: Allows the execution of code blocks containing impure functions.

        Description:

        If the code block to be executed contains an impure function, then
        the use of global and local contexts becomes more complex.

        execute_impure helps you do this appropriately.

        The crucial restrictions are (background, optional read):

          * The passed-in global context must be an actual dictionary. It is
          visible throughout the code block.

          * The passed-in local context is not visible inside the function,
          unless it is identical to the passed-in global context.

          * Any names defined in the code block top level (outside the
          function), become part of the passed-in local context, not
          necessarily part of the passed-in global context.

        Therefore (read this!):

          * If the function needs access to names from a passed-in context,
          that context must be global and must be a dict.

          * If the function needs access to names defined in the code block's
          top level (outside the function), including imports or other
          function definitions, then the passed-in local and global contexts
          must be identical, and must be a dict.

        To meet these requirements, execute_impure copies a context into a
        dict, then executes the code block with this dict serving as both
        local and global context.

        execute_impure also uses a shadow dictionary to track any calls to the
        context dict's __setitem__, allowing you to keep track of changes made
        to the context by the code block.

          * If a name is defined in the top level of the code block, then it
          will be saved in the shadow dictionary.

          * If a value in the context is a mutable object, then both the
          original context and the shadow dict hold references to it, and any
          changes to it will automatically be be reflected in the original
          context, not in the shadow dictionary.

          * Any global names defined inside a function in the code block (via
          the 'global' command) will not be reflected in the shadow dictionary,
          because the global context is always directly accessed by low-level
          c code (as of python versions through 3.2).

        Parameters:

            context: namespace in which to execute the code block(s)

            continue_on_errors: see method 'execute'

            clean_shadow: If True, then before returning the shadow dictionary,
            deletes from it all functions, methods, and items whose name begins
            with underscore.

        Returns the shadow dictionary, described above.

            A common usage would be to update the original context with the
            returned shadow. If the original context is a MultiContext, then
            by default the first subcontext would be updated with these
            shadowed names/values.

        """
        shadowed = ShadowDict(context)
        self.execute(shadowed, shadowed, continue_on_errors)
        shadow = shadowed.shadow
        if clean_shadow:
            # Fixme: clean_shadow should probably remove a few more types,
            # but these are the obvious ones.
            shadow = dict((name, value) for (name, value) in shadow.iteritems()
                          if name[0] != '_' and
                          type(value) not in (types.FunctionType,
                                              types.ModuleType))
        return shadow


    def invalidate_cache(self):
        """ Someone modified the block's internal ast. This method provides and
            explicit means to invalidating the cached _code object
        """
        self._code_invalidated = True

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

        inputs = set(inputs)
        outputs = set(outputs)

        # Look for results in the cache
        cache_key = (frozenset(inputs), frozenset(outputs))
        if cache_key in self.__restrictions:
            return self.__restrictions[cache_key]

        # Validate the method arguments.
        #
        # 'inputs' are allowed to be in the block inputs or outputs to allow
        # for restricting intermidiate inputs.
        if not (inputs or outputs):
            raise ValueError('Must provide inputs or outputs')
        if not inputs.issubset(self.inputs | self.outputs | self.fromimports):
            raise ValueError('Unknown inputs: %s' % (inputs - self.inputs - self.outputs - self.fromimports))
        if not outputs.issubset(self.all_outputs):
            raise ValueError('Unknown outputs: %s' %(outputs-self.all_outputs))

        # Validate the block to make sure it is safe for restriction
        if self.validate_for_restriction() is not None:
            raise RuntimeError("Block failed to validate")

        # If we don't decompose, then we are already as restricted as possible
        if self.sub_blocks is None:
            return self

        # we must keep a list of import blocks. Imports are lost because
        # they are not reachable during the reversing of the graph
        import_sub_blocks = []
        for sub_block in self.sub_blocks:
            if isinstance(sub_block.ast, compiler.ast.Import) or \
               isinstance(sub_block.ast, compiler.ast.From):
                import_sub_blocks.append(sub_block)

        # We use the mock constructors `In` and `Out` to separate input and
        # output names in the dep graph in order to avoid cyclic graphs (in
        # case input and output names overlap)
        in_, out = object(), object() # (singletons)
        In = lambda x: (x, in_)
        Out = lambda x: (x, out)

        def wrap_names(wrap):
            "Wrap names and leave everything else alone"
            def g(x):
                if isinstance(x, basestring):
                    return wrap(x)
                else:
                    return x
            return g

        # Decorate input names with `In` and output names with `Out` so that
        # `g` isn't cyclic
        g = map_keys(wrap_names(Out),
                map_values(lambda l: map(wrap_names(In), l), self._dep_graph))

        # Find the subgraph reachable from inputs, and then find its subgraph
        # reachable from outputs. (We could also flip the order.)
        if inputs:
            # look in the outputs for intermediate inputs
            intermediates = map(Out, self.outputs.intersection(inputs))
            inputs = inputs - self.outputs.intersection(inputs)

            # Find the intermediate's block node and replace it
            # with the intermediate value. This effectively cuts
            # the block's children off the tree. This means for
            # the code "c = a * b; d = c * 3", we are removing c's
            # dependency on "a" and "b"
            #
            # There is a special case which is handled here as well:
            # for the code "c = a * b; d = c * 3", is the user wants
            # to restrict the block with 'd' as an input, the result
            # is an empty sub-block
            for intermediate in intermediates:
                pruned_block = g[intermediate][0]

                # its possible someone tried to restrict an import,
                # which is not in the graph
                #fixme: uncommenting these breaks pruning intermediates, why is this here?
#                if not g.has_key(pruned_block):
#                    intermediates.remove(intermediate)
#                    continue

                # if intermediate is not removed, the resulting graph will
                # be cyclic
                g.pop(intermediate)

                pure_output = True
                for v in g.values():
                    if pruned_block in v:
                        pure_output = False
                        v.remove(pruned_block)
                        v.append(intermediate)
                if pure_output:
                    # pure outputs must be kept on the graph or else
                    # they will not be reachable
                    g[intermediate] = [Block("%s = %s" % \
                                        (intermediate[0], intermediate[0]))]

            inputs = map(In, inputs) + intermediates

            # if no inputs were valid, do not alter the graph
            if len(inputs) > 0:
                g = graph.reverse(graph.reachable_graph(graph.reverse(g), inputs))
        if outputs:
            outputs = map(Out, outputs)
            g = graph.reachable_graph(g, set(outputs).intersection(g.keys()))

        # Create a new block from the remaining sub-blocks (ordered imports
        # first, then input to output, ignoring the variables at the ends)
        # and give it our filename
        remaining_sub_blocks = [node for node in reversed(graph.topological_sort(g))
                       if isinstance(node, Block)]

        # trim out redundant imports which can occur if a restricted output is
        # one of the imports:
        for sub_block in remaining_sub_blocks:
            if sub_block in import_sub_blocks:
                remaining_sub_blocks.remove(sub_block)

        b = Block(import_sub_blocks + remaining_sub_blocks)
        b.filename = self.filename

        # Cache result
        self.__restrictions[cache_key] = b

        return b

    def get_function(self, inputs=[], outputs=[]):
        """Return a function which takes the list of input variables
        as arguments and returns the given output_list.

        These lists determine the calling order for the function.
        """
        if isinstance(outputs, basestring):
            outputs = [outputs]
        if isinstance(inputs, basestring):
            inputs = [inputs]
        block = self.restrict(inputs=inputs, outputs=outputs)
        # Speed up execution of the block
        block.no_filenames_in_tracebacks = True
        leni = len(inputs)
        leno = len(outputs)
        def simplefunc(*args):
            if len(args) != leni:
                raise ValueError("Must have %d inputs" % leni)
            namespace = {}
            for i, arg in enumerate(args):
                namespace[inputs[i]] = arg
            block.execute(namespace)
            if leno == 1:
                return namespace[outputs[0]]
            vals = []
            for name in outputs:
                vals.append(namespace[name])
            return tuple(vals)
        callstr = '(%s)'% ','.join(inputs)
        retstr = ','.join(outputs)
        simplefunc.__doc__ = "%s = <name>%s" % (retstr, callstr)
        simplefunc._block = block
        return simplefunc

    def validate_for_restriction(self):
        # Check to ensure that there is not sub_block that has the same
        # variable as an input and an output. Return the offending
        # sub_block if one exists, or return None if block is valid.
        if self.sub_blocks is None:
            if len(self.inputs.intersection(self.outputs)) > 0:
                return self
        else:
            for sb in self.sub_blocks:
                if len(sb.inputs.intersection(sb.outputs)) > 0:
                    return sb
        return None

    ###########################################################################
    # Block protected interface
    ###########################################################################

    # 'ast_tree' determines 'sub_blocks' and 'sub_blocks' determines 'ast_tree',
    # so when one changes we update the other. Both together represent the main
    # structure of the Block object and determine 'inputs', 'outputs',
    # 'conditional_outputs', '_dep_graph', and '_code'.
    #
    # We compute '_dep_graph' and '_code' only when necessary and avoid
    # redundant computation.

    # I don't think this is needed anymore since new AST uses Module([body])
    # not Module(Stmt([body])) like the old AST.
#    def _tidy_ast_tree(self):
#        if isinstance(self.ast_tree, Module):
#            self.ast_tree = self.ast_tree.body
#        if isinstance(self.ast_tree, stmt) and len(self.ast_tree._fields) == 1:
#            self.ast_tree = [node for node in self.ast_tree.iter_child_nodes()]

    def _structure_changed(self, name, new):
        if not self._updating_structure:
            try:
                self._updating_structure = True

                if name == 'ast_tree':
                    # Compute our new sub-blocks and give them our filename
                    sub_blocks = Block._decompose(self.ast_tree)
                    self.sub_blocks = sub_blocks
                    if self.sub_blocks is not None:
                        for b in self.sub_blocks:
                            b.filename = self.filename
                        # Policy: Only atomic blocks have filenames
                        self.filename = None

                elif name in ('sub_blocks', 'sub_blocks_items'):
                    self.ast_tree = Module([ b.ast_tree for b in self.sub_blocks ])

                else:
                    assert False

                # Invalidate caches
                self.__dep_graph_is_valid = False
                self.__restrictions.clear()
                self._stored_string = ''

                # update inputs and outputs
                self._clear_cache_inputs_and_outputs()

            finally:
                self._updating_structure = False

    def _clear_cache_inputs_and_outputs(self):
        self._inputs = None
        self._outputs = None
        self._conditional_outputs = None
        self._const_assign = None
        self._fromimports = None
        self._imports_ast = None

    def _set_inputs_and_outputs(self):
        if self.ast_tree is None:
            return

        nf = NameFinder()
        nf.visit(self.ast_tree)
        self._inputs = set(nf.free)
        self._outputs = set(nf.locals)
        self._conditional_outputs = set(nf.conditional_locals)
        temp = [unparse(x).strip() for x in nf.constlist]
        temp2 = [x.split('=')[0].strip() for x in temp]
        self._const_assign = (set(temp2), temp)
        self._fromimports = set(nf.fromimports)
        self._outputs -= self.fromimports
        self._imports_ast = nf.imports

    def _get_inputs(self):
        if self._inputs is None:
            self._set_inputs_and_outputs()
        return self._inputs

    def _get_outputs(self):
        if self._outputs is None:
            self._set_inputs_and_outputs()
        return self._outputs

    def _get_conditional_outputs(self):
        if self._conditional_outputs is None:
            self._set_inputs_and_outputs()
        return self._conditional_outputs

    def _get_const_assign(self):
        if self._const_assign is None:
            self._set_inputs_and_outputs()
        return self._const_assign

    def _get_fromimports(self):
        if self._fromimports is None:
            self._set_inputs_and_outputs()
        return self._fromimports

    def _get_imports_ast(self):
        if self._imports_ast is None:
            self._set_inputs_and_outputs()
        return self._imports_ast

    def _get_codestring(self):
        if self._stored_string != '':
            return self._stored_string
        else:
            return unparse(self.ast_tree)

    @cached_property
    def _get__code(self):
        # Policy: our AST is either a Module or something that fits in a
        # Stmt. (Note that a Stmt fits into a Stmt.)
        ast_tree = self.ast_tree
        if not isinstance(ast, Module):
            ast_tree = Module(None, stmt([ast_tree]))

        # Make a useful filename to display in tracebacks
        if not self.no_filenames_in_tracebacks:
            if self.filename is not None:
                filename = self.filename
            else:
                filename = '<%r>' % self
        else:
            filename = '(Block with filename suppressed)'

        return compile_ast(ast_tree, filename, 'exec')

    def _get__dep_graph(self):

        # Cache dep graphs
        if not self.__dep_graph_is_valid:

            inputs, outputs, conditional_outputs, self.__dep_graph = \
                Block._compute_dependencies(self.sub_blocks)

            self.__dep_graph_is_valid = True

        return self.__dep_graph

    ###########################################################################
    # Block class interface
    ###########################################################################

    @classmethod
    def from_file(cls, f): # (XXX Deprecated)
        'Create a Block from a source file.'
        import warnings
        warnings.warn(DeprecationWarning("Use Block.__init__(file=...)"))
        return cls(file=f)

    @classmethod
    def from_string(cls, s): # (XXX Deprecated)
        'Create a Block from a code string.'
        import warnings
        warnings.warn(DeprecationWarning("Use Block.__init__"))
        return cls(s)

    ###########################################################################
    # Block class protected interface
    ###########################################################################

    @classmethod
    def _decompose(cls, ast_tree):
        ''' Decompose an AST into a sequence of blocks, if possible.

            Returns 'None' on failure.
        '''
        assert isinstance(ast_tree, AST)

        # TODO Look within 'for', 'if', 'try', etc. (#1165)
        if isinstance(ast_tree, Module):
            result = [cls._decompose(node) for node in ast_tree.body]
        elif isinstance(ast_tree, stmt):
            if len(ast_tree._fields) == 0:
                result = [Block(ast_tree)]
            elif len(ast_tree._fields) == 1:
                # Treat 'Stmt([node])' the same as 'node'
                result = cls._decompose(getattr(ast_tree, ast_tree._fields[0]))
            else:
                result = Block(ast_tree)
        else:
            result = [Block(ast_tree)]

        return result

    ###########################################################################
    # Block static protected interface
    ###########################################################################

    @staticmethod
    def _compute_dependencies(blocks):
        ''' Given a sequence of blocks, compute the aggregate inputs, outputs,
            and dependency graph.

            Parameters
            ----------
            blocks : List(Block)
              A list of blocks in order of execution to "tie-up" into a larger,
              single block.

            Returns
            -------
            inputs : Set(Str)
              The input parameters to the new block.

            outputs : Set(Str)
              The output parameters to the new block.

            conditional_outputs : Set(Str)
              The conditional output parameters to the new block, i.e. names
              that might or might not be defined by an arbitrary execution of
              the block.

            dep_graph : Dict(Either(Block, Str), List(Either(Block,Str)))
              The dependency graph (directed, acyclic) relating the blocks from
              the given sequence: block A depends on block B iff an output from
              B is used as an input to A.
              Additionally, the names of the inputs and outputs for the new
              block are included in the graph to capture their dependency
              relations to the contained blocks: name X depends on block A iff
              X is an output of A, and block A depends on name X iff X is an
              input to A.

            (Alternative: make each Block track its own dependencies)
        '''

        # An ad-hoc graph interface
        class Graph(dict):
            def link(self, k, v):
                return self.setdefault(k, set()).add(v)
            def unlink_from(self, k):
                if k in self:
                    del self[k]

        # Deferred computations
        deferred = set()

        # Build dep_graph: a not transitively closed dependency graph that
        # relates blocks to the blocks and inputs they depend on, and outputs
        # to the last block that modifies or creates them
        inputs, outputs, conditional_outputs = set(), set(), set()
        dep_graph, env = Graph(), {}
        for b in blocks:

            # 'b' depends on the provider for each of its inputs or, if none
            # exists, it depends on the inputs themselves (as inputs to the
            # aggregate block). If a name is provided only conditionally, then
            # 'b' depends on both the provider and the input.
            for i in b.inputs:
                # We need to make sure that dotted names are not included if
                # their parent module or object is already in env.
                process_i, prefix, suffix = True, '', i
                while '.' in suffix:
                    if prefix == '':
                        prefix = suffix[:suffix.find('.')]
                    else:
                        prefix += suffix[:suffix.find('.')]
                    if prefix in env:
                        dep_graph.link(b, env[prefix])
                        process_i = False
                        break
                    suffix = suffix[suffix.find('.')+1:]

                if process_i:
                    if i in env:
                        dep_graph.link(b, env[i])
                    if i not in env or i in conditional_outputs:
                        inputs.add(i)
                        dep_graph.link(b, i)

            for c in b.conditional_outputs:

                # 'b's outputs depend only on 'b'
                dep_graph.unlink_from(c)
                dep_graph.link(c, b)

                # 'b' depends on the provider for each of its conditional
                # outputs or, if none exists and the end result has an input of
                # the same name, 'b' depends on that input. (We defer the
                # latter test to check against the final set of inputs rather
                # than just the inputs we've found so far.)
                if c in env:
                    dep_graph.link(b, env[c])
                else:
                    def f(b=b, c=c):
                        if c in inputs:
                            dep_graph.link(b, c)
                    deferred.add(f)

                # 'b' contributes conditional outputs to the aggregate block
                # unless they are already unconditional
                if c not in outputs:
                    conditional_outputs.add(c)

                # 'b' becomes the provider for its conditional outputs
                env[c] = b

            for o in b.outputs:

                # 'b's outputs depend only on 'b'
                dep_graph.unlink_from(o)
                dep_graph.link(o, b)

                # 'b' contributes its outputs to the aggregate block -- as
                # unconditional outputs
                outputs.add(o)
                conditional_outputs.discard(o)

                # 'b' becomes the provider for its outputs
                env[o] = b

        # Run deferred computations
        for f in deferred:
            f()

        return inputs, outputs, conditional_outputs, dep_graph

class Expression(HasTraits):

    # TODO Unify with Block (factor things out of Block)

    ###########################################################################
    # Expression traits
    ###########################################################################

    inputs = Instance(set)
    outputs = Instance(set)

    uuid = Instance(UUID)
    _uuid_default = lambda self: uuid4()

    _code = Property

    ###########################################################################
    # object interface
    ###########################################################################

    def __init__(self, ast, inputs, outputs):
        super(Expression, self).__init__()

        self._ast = ast
        self.inputs, self.outputs = set(inputs), set(outputs)

    ###########################################################################
    # Expression public interface
    ###########################################################################

    def evaluate(self, context):
        return eval(self._code, {}, context)

    ###########################################################################
    # Expression protected interface
    ###########################################################################

    ###########################################################################
    # Expression class interface
    ###########################################################################

    @classmethod
    def from_string(cls, s):
        ast_tree = ast.parse(s, mode='eval')
        ast_tree = BlockTransformer().visit(ast_tree)
        assert isinstance(ast_tree, compiler.ast.Expression)
        v = compiler.walk(ast_tree, NameFinder())
        return Expression(ast_tree, v.free, v.locals)

################################################################################
# Util
################################################################################

def to_block(x):
    "Coerce 'x' to a Block without creating a copy if it's one already"
    if isinstance(x, Block):
        return x
    else:
        return Block(x)
