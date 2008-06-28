

import pdb
import sys, os
import linecache
import re

from block import Block

#single_quotes = re.compile("'.*'")
#double_quotes = re.compile('".*"')
#triple_quotes = re.compile('""".*"""')

# Perhaps we can remove docstrings at some point, but
#  probably not worth it.
def strip_whitespace(source, name):
    # Expand tabs to avoid any confusion.
    wsource = [l.expandtabs(4) for l in source]

    # Remove any code definition, and space lines
    #  at the beginning
    for i, line in enumerate(wsource):
        if line.isspace():
            continue
        if line.startswith('def %s' % name):
            continue
        break
    wsource = wsource[i:]

    # Detect the indentation level
    done = False
    for line in wsource:
        for col,char in enumerate(line):
            if char != ' ':
                done = True
                break
        if done:
            break
    # Now we know how much leading space there is in the code.  Next, we
    # extract up to the first line that has less indentation.
    # WARNINGS: we skip comments that may be misindented, but we do NOT yet
    # detect triple quoted strings that may have flush left text.
    for lno,line in enumerate(wsource):
        lead = line[:col]
        if lead.isspace():
            continue
        else:
            if not lead.lstrip().startswith('#'):
                break
    if (lno+1 == len(wsource)):
        lno = lno + 1
    # The real source is up to lno
    src_lines = [l[col:] for l in wsource[:lno]]
    src = ''.join(src_lines)
    #print 'SRC:\n<<<<<<<>>>>>>>\n%s<<<<<>>>>>>' % src  # dbg
    return src

def findsource_file(f, name):
    lines = linecache.getlines(f.f_code.co_filename)
    wsource = lines[f.f_lineno:]
    return strip_whitespace(wsource, name)

def findsource_ipython(f, name):
    from IPython import ipapi
    ip = ipapi.get()
    wsource = [l+'\n' for l in
               ip.IP.input_hist_raw[-1].splitlines()[1:]]
    return strip_whitespace(wsource, name)


def func2str(func,backframes=1):
    """Decorator to turn a code-block inside of a function to
    a string.

    @func2str
    def code():
        c = a + b
        d = a - b

    This will return a string of code: 'a = 3\nb = 4\nc = a + b\n'
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
    a code-object.

    @func2co
    def code():
        c = a + b
        d = a - b

    This will return code as a compiled 'anonymous' code object
    """
    s = func2str(func, backframes=2)
    return compile(s, 'anonymous', 'exec')

def func2block(func):
    """Decorator to turn a code-block defined as a function into
    a code-object.

    @func2block
    def code():
        d = a + b
        c = a - b

    This will return the code piece as a Block.
    """
    s = func2str(func, backframes=2)
    return Block(s)
    
    
