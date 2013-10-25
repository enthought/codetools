
.. _roadmap:

******************
CodeTools Roadmap
******************

This document exists as a place to keep track of proposed enhancements to
CodeTools and indicate where development effort could profitably be spent.

Things That Won't Change
========================

* There will be a Block class:

  - that accepts code and ASTs and other Blocks for initialization.

  - that has an :meth:`execute` method with similar semantics to an :func:`exec`
    statement
  
  - that has :attr:`inputs`, :attr:`outputs` and :attr:`fromimport` attributes,
    as well as some sort of conditional output attribute
  
* There will be a DataContext class very similar to the current one.  I
  don't think that there will be much change needed in this other than
  changes/improvements based on changes to the traits API

* The MultiContext, AdaptedDataContext, TraitslikeContextWrapper objects
  should be fairly stable.

Blocks
======

Language Support
----------------

The biggest deficiency with blocks right now is that they don't fully support
all Python language features, such as:

* list comprehensions
* generator expressions

A near term goal should be that code should be able to make a round-trip
through a block without changing the outcome of executing it::

   exec code
   Block(code).execute()
   exec unparse(Block(code).ast)

should (in the absence of other manipulations) do the same thing, and
``unparse(Block(code).ast)`` should produce code that is as close as practical
to the original code block.

Speed
-----

Currently whenever a Block is created it immediately parses the code to an
AST.  This is not a particularly fast operation, and can cause slowdowns if
a large number of Blocks are created in quick succession.  Deferring this
AST generation using Traits properties would alleviate this somewhat, but
would require a refactor of the Block object.

It may be worthwhile doing some serious profiling of the parser and compiler
to see if there are places where speed can be improved.

New Functionality
-----------------

There are almost certainly new pieces of functionality that may be worth
adding:

* improved branching analysis tools --- what variables depend on what other
  variables
* common AST manipulation routines in the spirit of codetools.blocks.rename


Contexts
========

The main area that has room for development in the context packages is adding
to the provided collections of filters and adapters.

Execution
=========

There should be a robust and general ExecutionManager class that listens to
a Context and then executes a Block in that (or a related) Context.  This
would essentially split this functionality out from the ExecutingContext
class.


New Modules
===========

ByteCodeTools
-------------

There may be a place for a library that provides a rich and consistent
interface for bytecode manipulation.  Currently the only place where we do
this sort of manipulation is in the :mod:`context_function` module, and there the
bytecode substitution is fairly simple.

For example, there may be a more efficient way to provide the functionality of
:mod:`codetools.blocks.rename` by manipulating code objects and bytecode rather
than AST.

