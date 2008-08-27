
.. _tutorial:

********
Tutorial
********

This tutorial introduces the key concepts behind the CodeTools modules, as
well as highlighting some of their potential applications.


Introduction
============

The two building-blocks of the CodeTools system are the Block object and the
DataContext object (and its various subclasses).

A Block simply holds a set of executable content, such as might be run by a
Python exec command.  However, unlike a simple code string, the Block object
performs analysis of the code it contains so that it can identify which of its
variables depend on which other variables.

A DataContext can be thought of as a Traits-aware dictionary object.  The base
DataContext simply emits Traits events whenever an item added, modified or
deleted from it.  Subclasses allow more sophisticated actions to take place
on access or modification.

This system of code and data objects evolved out of Enthought's scientific
applications as a common pattern where a series of computationally expensive
transformations and calculations needed to be repeatedly performed on
different sets of data, often with simple permutations if inputs into the
calculation blocks, and often in interactive situations where responsiveness
is important.  The Block object, by being aware of how data flows through the
code that it contains, can restrict the code that it actually needs to execute
based on a permutation of an input.  The DataContext, by being able to trigger
Traits events whenever it changes can call upon a Block to recalculate
dependent variables, and user-interface objects can listen to the events it
generates to update based upon changes in its namespace.

Subclasses of the DataContext extend its functionality to provide
functionality such as unit conversion, data masking, name translation and
datatype separation.

Blocks
======

Creating a Block object is as simple as invoking it on a string containing
some Python code::

    >>> from enthought.blocks.api import Block
    >>>
    >>> b = Block("""# my calculations
    ... velocity = distance/time
    ... momentum = mass*velocity
    ... """)

The code in the block can be executed by using its ``execute`` method in much
the same way that the ``exec`` statement works::

    >>> global_namespace = {}
    >>> local_namespace = {'distance': 10.0, 'time': 2.5, 'mass': 3.0}
    >>> b.execute(local_namespace, global_namespace)

After this code, the variables ``local_namespace`` and ``global_namespace``
hold the same contents as if the Block's code had been executed by the
``exec`` statement.  In particular::

    >>> local_namespace
    {'distance': 10.0, 'mass': 3.0, 'time': 2.5, 'velocity': 4.0, 'momentum': 12.0}

Restricting Execution
---------------------

Where the Block object comes into is that it is aware of which variables are
dependent on which other variables within its code.  This allows you to
restrict the code which is executed::

    >>> restricted_block = b.restrict(inputs=('mass',))

This restricted block consists of every line that depends on the variable
``mass`` in the original code block.  In this case this is the single line::

    momentum = mass*velocity

Internally the Block object maintains a representation of the code block as
an abstract syntax tree from the Python standard library `compiler
package <http://docs.python.org/lib/compiler.html>`_.  This representation
is not particularly human-friendly, but the ``unparse`` function allows the
reconstruction of Python source::

    >>> restricted_block.ast
    Assign([AssName('momentum', 'OP_ASSIGN')], Mul((Name('mass'), Name('velocity'))))
    >>> from enthought.blocks.api import unparse
    >>> unparse(restricted_block.ast)
    'momentum = mass*velocity'

This allows us to perform the minimum amount of re-calculation in response to
changes in the inputs.  For example, if we change ``mass`` in the local
name space, then we only need to execute the restricted block which depends
upon ``mass`` as input::

    >>> local_namespace['mass'] = 4.0
    >>> restricted_block.execute(local_namespace, global_namespace)
    >>> local_namespace
    {'distance': 10.0, 'mass': 3.0, 'time': 2.5, 'velocity': 4.0, 'momentum': 16.0}

DataContexts
============