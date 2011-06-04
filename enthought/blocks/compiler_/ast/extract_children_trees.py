#!/usr/bin/env python

# Construct 'getChildrenTree' methods for each subclass of compiler.ast.Node
# based on their implementations of __repr__.

import os.path, re, sys, time

from traits.util.functional import partial, compose

def grep(pattern, lines):
    for line in lines:
        if re.search(pattern, line):
            yield line

def main():

    try:
        [_, file] = sys.argv
    except (ValueError, IOError):
        print >>sys.stderr, 'Usage: %s /path/to/compiler.ast.py' % sys.argv[0]
        sys.exit(1)
    s = open(file).read()

    print '# Extend compiler.ast with a structure-preserving children query.'
    print '#'
    print '# Automatically generated on %s from:' % time.asctime()
    print '#   %s' % os.path.realpath(file)
    print
    print 'import compiler.ast as ast'
    print

    # (A line starts with 'return "' iff it's a one-line __repr__ definition)
    for line in grep('return "', open(file).read().split('\n')):

        line = re.sub('repr[(](.*?)[)]', r'"\1"', line)
        class_, children = re.match('^\s*return "(\w+)(.*)$', line).groups()
        children = eval('"' + children)

        # tuples -> list
        assert children[0] == '(' and children[-1] == ')'
        children = '[%s]' % children[1:-1]

        # Construct 'getChildrenTree' definition
        print 'ast.%s.getChildrenTree = lambda self: %s' % (class_, children)

if __name__ == '__main__':
    main()
