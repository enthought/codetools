from compiler.ast import Node

def similar(a,b):
    'Whether two ASTs are structurally equivalent'
    return repr(a) == repr(b)

def hash_structure(a):
    return hash(repr(a))
