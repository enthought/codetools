#
# (C) Copyright 2013 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is open source software distributed according to the terms in
# LICENSE.txt
#
from __future__ import absolute_import

# python standard library imports
from UserDict import DictMixin

# Enthought library imports
from .adapted_data_context import AdaptedDataContext

class IterableAdaptedDataContext(AdaptedDataContext):
    """ An AdaptedDataContext whose iteration includes any key mapped
    by any NameAdapter to an existing key.

    This is useful for presenting the user with a list of available names
    (keys). It is not so useful for obtaining a list of values to be operated
    on, since any values whose keys are thus remapped would be included more
    than once.

    Fixme: This separate subclass may not be necessary.
    Perhaps these methods could simply be moved into AdaptedDataContext,
    but for now, to ensure no old code is broken, we keep them separate.
    """
    # Fixme:? For consistency with AdaptedDataContext,
    # this could use a mixin, but to what purpose?

    def keys(self):
        """ Return the list of keys available in the adapted context.
        Does not include any key which is mapped by an adapter to an
        undefined key (i.e. which would fail as an argument to __getitem__
        or return False as an argument to __contains__).
        """
        _keys = set(self.subcontext.keys())

        # Check each adapter's key map.  The adapters are listed in order
        # of increasing distance from the subcontext, so later adapters
        # may map back to earlier adapters.
        for adapter in self._adapters:
            if hasattr(adapter, 'adapt_keys') and hasattr(adapter,
                                                          'adapt_name') :
                _keys.update(key for key in adapter.adapt_keys()
                             if adapter.adapt_name(self.subcontext, key)
                             in _keys)
        return list(_keys)


    """ Expose DictMixin's __contains__ method over DataContext's, which is
    inherited by AdaptedDataContext but only looks at the subcontext, not at
    adapters. In contrast, DictMixin tries to use the key and returns false if
    it fails.

    Fixme:? Might be more efficient to explicitly check subcontext first.
    """
    __contains__ = DictMixin.__contains__

