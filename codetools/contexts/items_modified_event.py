#
# (C) Copyright 2013 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is open source software distributed according to the terms in
# LICENSE.txt
#
from __future__ import absolute_import

from traits.api import Str, List, Vetoable, VetoableEvent, Any


class ItemsModified ( Vetoable ):
    """ Type of event fired when a DataContext has values added or removed.
    """

    context = Any #Instance('codetools.contexts.i_context.IContext')
    added = List(Str)
    removed = List(Str)
    modified = List(Str)

    def __repr__(self):
        return ('%s(context=%r, added=%r, removed=%r, modified=%r)' %
            (type(self).__name__, self.context, self.added, self.removed,
                self.modified))

# Define an Event trait which accepts an ItemsModified object:
ItemsModifiedEvent = VetoableEvent( ItemsModified )
