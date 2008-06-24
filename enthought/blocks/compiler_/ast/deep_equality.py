'Extend base class compiler.ast.Node with deep equality.'

from compiler.ast import Node

import ast

Node.__eq__ = ast.similar
Node.__ne__ = lambda self, other: not (self == other)
Node.__hash__ = ast.hash_structure
