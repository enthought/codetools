

import pdb
import sys, os
import linecache
import re

from block import Block

def _detect_indentation_level(source):
    # Detect the indentation level
    done = False
    for line in source:
        for col,char in enumerate(line):
            if char != ' ':
                done = True
                break
        if done:
            break
    return col

def _extract_indented_part(source, col):
    # Now we know how much leading space there is in the code.  Next, we
    # extract up to the first line that has less indentation.
    #  We skip comments that may be misindented and detect triple quoted
    #  strings and ignore indentation inside them.
    triple_string = 0
    src_lines = []
    doc_lines = []
    for lno,line in enumerate(source):
        if triple_string:
            if line.rstrip().endswith('"""'):
                triple_string = 0
            doc_lines.append(line)
            continue
        lead = line[:col]
        if lead.isspace():  # indented part
            code = line[col:]
            if code.startswith('"""'):
                triple_string = 1
                doc_lines.append(code)
            else:
                src_lines.append(code)
            continue
        if lead.lstrip().startswith('#'):  # comment line
            src_lines.append(line.lstrip())
        else:
            break
    src = ''.join(src_lines)
    return src, "".join(doc_lines)

def _remove_head(source, name):
    # Remove any code definition, and space lines
    #  at the beginning
    for i, line in enumerate(source):
        if line.isspace():
            continue
        if line.startswith('def %s' % name):
            continue
        break
    if len(source) > 0:
        source = source[i:]
    return source

def strip_whitespace(source, name, spaces_for_tab):
    # Expand tabs to avoid any confusion.
    wsource = [l.expandtabs(spaces_for_tab) for l in source]

    wsource = _remove_head(wsource, name)
    col = _detect_indentation_level(wsource)
    src, doc = _extract_indented_part(wsource, col)

    #print 'SRC:\n<<<<<<<>>>>>>>\n%s<<<<<>>>>>>' % src  # dbg
    return src

def findsource_file(f, name):
    lines = linecache.getlines(f.f_code.co_filename)
    wsource = lines[f.f_lineno:]
    return strip_whitespace(wsource, name, 8)

def findsource_ipython(f, name):
    from IPython import ipapi
    ip = ipapi.get()
    wsource = [l+'\n' for l in
               ip.IP.input_hist_raw[-1].splitlines()[1:]]
    return strip_whitespace(wsource, name, 4)


def func2str(func,backframes=1):
    """Decorator to turn a code-block inside of a function to
    a string::
    
        @func2str
        def code():
            c = a + b
            d = a - b

    This returns a string of code: ``a = 3\\nb = 4\\nc = a + b\\n``
    """
    callframe = sys._getframe(backframes)
    lineno = callframe.f_lineno
    filename = callframe.f_code.co_filename
    if filename == '<stdin>':
        raise ValueError, "Decorator can't be used here."
    elif filename == '<ipython console>':
        s = findsource_ipython(callframe, func.func_name)
    else:
        s = findsource_file(callframe, func.func_name)
    return s
    
def func2co(func):
    """Decorator to turn a code-block defined as a function into
    a code-object::

        @func2co
        def code():
            c = a + b
            d = a - b

    This returns code as a compiled 'anonymous' code object.
    """
    s = func2str(func, backframes=2)
    return compile(s, 'anonymous', 'exec')

def func2block(func):
    """Decorator to turn a code-block defined as a function into
    a code-object::

        @func2block
        def code():
            d = a + b
            c = a - b

    This returns the code piece as a Block.
    """
    s = func2str(func, backframes=2)
    return Block(s)
    
    
