The Block-Context-Execution Manager Pattern
===========================================

The last example of the previous section is an instance of a pattern that has
been found to work very well at Enthought for the rapid development of
scientific applications. In principle it consists of 3 components:

* **Block:** an object that executes code in a namespace and knows its
  inputs and outputs.
* **Context:** a namespace that generates events when modified.
* **Execution Manager:** an object that listens for changes in the Context,
  and when a Block's inputs change, tells the Block to execute.

This is not an unfamiliar model: it's how most spreadsheet applications work.
You have the spreadsheet application itself (the Execution Manager), the
values contained in the cells (the Context), and the the functions and scripts
which perform the computations (the Block).

The example from the previous section might seem like an awful lot of
work to replace what, as far as basic computation is concerned, could be
implemented with a fairly simple HasTraits class like this::

    class DoItAll(HasTraits):
        # inputs
        distance = Float
        time = Float
        mass = Float
        
        # outputs
        velocity = Float
        momentum = Float
    
        def calculate(self):
            self.velocity = self.distance/self.time
            self.momentum = self.mass*self.velocity

However, the Block-Context-Execution Manager pattern gives us the following
advantages:

* ability to restrict computations to the bare minimum required
* immediate feedback on computations while they occur
* automated recalculation in response to changes
* (perhaps most importantly) almost complete separation between the
  application code (the execution manager and UI components), the
  computation code, and the data

Actually, by using Traits properties you can get the first three of these ---
although the code will become more and more complex as the computations get
longer.

The last point, however, is very powerful and is something that you cannot get
with an all-in-one approach.  It means that computational code can be
written almost completely independently of application and UI code.  With
appropriate ``try ... except ...`` blocks, the inevitable errors in the
calculation blocks (particularly if user-supplied) or problems with the data
can be contained. The Context is well-suited to being the Model in
a Model-View-Controller UI pattern, particularly since it uses Traits.

And it encourages code re-use.  In fact, a well-written execution manager has
the potential to be a complete application framework which can be repurposed
to different domains by simply replacing the blocks that it executes.
Similarly, well-written Blocks will most likely have clean libraries associated
with them and can be re-used with different types of variables. (At Enthought
it is common to use the same Block code with scalars in the UI and with arrays
to produce plots.)

It is worth noting that the roles do not have to be kept completely separate.
There are situations where bundling together the Execution Manager with the
Block (to make a smart block that re-executes whenever it needs to) or a
DataContext (to make a smart data set) makes sense.  The ExecutingContext
class in :mod:`enthought.execution.api` is precisely such an example: it 
combines a DataContext and a listener to automatically execute.


