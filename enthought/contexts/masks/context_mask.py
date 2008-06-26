""" Class for masking geo_context with conditions on indices
"""

#------------------------------------------------------------------------------
#  ContextMask class
#------------------------------------------------------------------------------

class ContextMask:
    """ BaseClass that is used for implementing with-statement

        Derived classes of this base class will override the 'get_indices'
        method to obtain the right set of indices, depending on the expected
        behavior of the mask. They could be several applications of masks:
        1. Related to index of the context,
        2. Related to names in the dictionary of the context,
        etc...

    """

    def __init__(self, context, condition, value_dict):
        """ Condition should be a string saying 'index < <value>'
        """

        self.indices = self.get_indices(condition, context)

        if len(self.indices):
            self.context = context
            self.value_dict = value_dict

            self.init_value_dict = {}
            for name in self.context.keys():
                self.init_value_dict[name] = self.context[name][self.indices]


    def __enter__(self):
        """ Method to be overwritten for a mask class.

            This is the block that is after the try statement, in the
            try-finally block obtained equivalent to the with statement.

        """

        if len(self.indices):
            for name in self.context.keys():
                if self.value_dict.has_key(name):
                    self.context[name][self.indices] = self.value_dict[name]

        return self.context


    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Method to be overwritten for a mask class

            This is the block that is after the finally statement, in the
            try-finally block obtained equivalent to the with statement.

        """

        # Revert all the changes done in __enter__ method.
        if len(self.indices):
            for name in self.context.keys():
                if self.value_dict.has_key(name):
                    self.context[name][self.indices] = \
                                    self.init_value_dict[name]

        return self.context


    #---------------------------------------------------------------------------
    #  ContextMask interface
    #---------------------------------------------------------------------------

    def get_indices(self, condition, context=None):
        """ This method will return the right set of indices in order to
            obtain the expected behavior of the mask.
        """

        raise NotImplementedError


### EOF ------------------------------------------------------------------------
