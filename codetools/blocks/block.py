'''
Created on Aug 4, 2011

@author: sean
'''
from codetools.blocks.smart_code import SmartCode
from codetools.blocks.lego import split
from asttools import conditional_lhs
from asttools.visitors.assign_visitor import rhs
from traits.api import HasTraits, Instance, List
from traceback import format_exc

from codetools.blocks.util.uuid import UUID, uuid4
import inspect
import abc

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

    uuid = Instance(UUID)
    _uuid_default = lambda self: uuid4()

    __this = Instance('Block') # (traits.This scopes dynamically (#986))
    sub_blocks = List(__this)


    def __init__(self, x=(), file=None, grouped=False, inner=None, **kw):

        super(Block, self).__init__(**kw)

        if inner is not None:
            self.scode = inner
        else:
            is_file_object = lambda o: hasattr(o, 'read') and hasattr(o, 'name')

            if file is not None:
                # Turn 'file' into a file object and move to 'x'
                if isinstance(file, basestring):
                    file = open(file)
                elif not is_file_object(file):
                    raise ValueError("Expected 'file' to be a file or string, "
                                     "got %r" % file)
                x = file


            # 'x': file object -> string
            if is_file_object(x):
                source = None
                file = x
            else:
                source = x
                file = None

            from ..util.sequence import is_sequence
            if isinstance(x, Block):
                self.scode = x.scode
            elif is_sequence(x) and not isinstance(x, basestring):
                from codetools.blocks.lego import join as join_code
                self.scode = join_code(Block(sub_block) for sub_block in x)
            else:
                self.scode = SmartCode(source, file, ast=None, path=None)

        self.conditional_outputs, self.outputs = conditional_lhs(self.scode.ast)

    def __repr__(self):
        return '%s(uuid=%s)' % (self.__class__.__name__, self.uuid)

    def __str__(self):
        return repr(self) # TODO Unparse ast (2.5) (cf. #1167)

    @property
    def ast(self):
        return self.scode.ast

    def _sub_blocks_default(self):
        return [Block(inner=sub_block) for sub_block in split(self.scode, reversed=False)]

    @property
    def all_outputs(self):
        return self.conditional_outputs | self.outputs

    @property
    def inputs(self):
        return rhs(self.scode.ast) - self.all_outputs

    def restrict(self, inputs=(), outputs=()):
        return Block(inner=self.scode.restrict(inputs, outputs))

    def execute(self, local_context, global_context={}, continue_on_errors=False):

        """Execute the block in local_context, optionally specifying a global
        context.  If continue_on_errors is specified, continue executing code after
        an exception is thrown and throw the exceptions at the end of execution.
        if more than one exception was thrown, combine them in a CompositeException"""
        # To get tracebacks to show the right filename for any line in any
        # sub-block, we need each sub-block to compile its own '_code' since a
        # code object only keeps one filename. This is slow, so we give the
        # user the option 'no_filenames_in_tracebacks' to gain speed but lose
        # readability of tracebacks.

        if not continue_on_errors:
            eval(self.scode.code, global_context, local_context)
        else:
            if continue_on_errors:
                exceptions = []
                for block in self.sub_blocks:
                    try:
                        block.execute(local_context, global_context)
                    except Exception, e:
                        # save the current traceback
                        e.traceback = format_exc()
                        exceptions.append(e)
                if exceptions:
                    if len(exceptions) > 1:
                        raise CompositeException(exceptions)
                    else:
                        raise exceptions[0]
        return

    def is_empty(self):
        """ Return true if 'block' has an empty AST.
        """

        return len(self.ast.body) == 0

    def get_function(self, inputs=(), outputs=()):
        raise NotImplementedError("")

    def remove_sub_block(self, uuid):
        raise NotImplementedError("")

def to_block(x):
    "Coerce 'x' to a Block without creating a copy if it's one already"
    if isinstance(x, Block):
        return x
    else:
        return Block(x)
