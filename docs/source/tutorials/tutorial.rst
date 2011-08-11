
.. _tutorial:

******************
CodeTools Tutorial
******************

.. epigraph::

    Namespaces are one honking great idea --- let's do more of those!
    
    --- Tim Peters, *The Zen of Python* (:pep:`20`)

This tutorial introduces the key concepts behind the CodeTools modules, as
well as highlighting some of their potential applications.  This tutorial
assumes some familiarity with Traits, and uses Chaco to illustrate some
potential uses.  Some familiarity with Numpy is also potentially useful for
the more involved examples. 

The two building-blocks of the CodeTools system are the Block class and the
DataContext class (and its various subclasses).

A Block object simply holds a set of executable content, such as might be run by a
Python exec command.  However, unlike a simple code string, the Block object
performs analysis of the code it contains so that it can identify which of its
variables depend on which other variables.

A DataContext can be thought of as a Traits-aware dictionary object.  The base
DataContext simply emits Traits events whenever an item is added, modified or
deleted. Subclasses allow more sophisticated actions to take place
on access or modification.

This system of code and data objects evolved out of Enthought's scientific
applications as a common pattern where a series of computationally expensive
transformations and calculations needed to be repeatedly performed on
different sets of data. These calculations often involved with simple 
permutations of inputs into the calculation blocks, and often were applied in
interactive situations where responsiveness
is important.  The Block object, by being aware of how data flows through the
code that it contains, can restrict the code that it actually needs to execute
based on a permutation of an input.  The DataContext, by being able to trigger
Traits events whenever it changes, can call upon a Block to recalculate
dependent variables, and user-interface objects can listen to the events it
generates to update based upon changes in its namespace.

Subclasses of the DataContext class extend its functionality to provide
functionality such as unit conversion, data masking, name translation and
datatype separation.

Put together, these concepts allow the creation of applications where the
science code and the underlying application code are kept almost completely
separate.

.. rubric:: Tutorial Sections

.. toctree::
   :maxdepth: 2
   
   tut_blocks.rst
   tut_datacontexts.rst
   tut_bcem_pattern.rst
   tut_tcw.rst
   tut_multicontext.rst
   tut_adapted.rst
   tut_cxt_functions.rst
   