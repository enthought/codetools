# Helper methods for the context package.

from numpy import ndarray

def compare_objects(object1, object2):
    """ Do a rich comparison of 2 given objects
    """

    # Reject objects which are strictly not the same type. This glosses over
    # ints and floats which compare equal and also instances where one is
    # a subclass of the other's class.
    if type(object1) != type(object2):
        return False

    # Specially handle numpy arrays and subclasses of same.
    if isinstance(object1, ndarray):
        check_equal = object1 == object2
        if isinstance(check_equal, ndarray):
            return check_equal.all()

    # We will handle dicts, lists, and tuples specially in order to recursively
    # use this comparision function for their innards. Otherwise, let == do it
    # for us.
    if not isinstance(object1, (dict, list, tuple)):
        return object1 == object2

    if isinstance(object1, dict):
        check_equal = compare_objects(set(object1.keys()), set(object2.keys()))

        if not check_equal:
            return False

        for k in object1.keys():
            check_equal = compare_objects(object1[k], object2[k])
            if not check_equal:
                return False

        return True

    # Return early if the sequences do not have the same length.
    if len(object1) != len(object2):
        return False

    # Compare each of the items to each other.
    for i in range(len(object1)):
        check_equal = compare_objects(object1[i], object2[i])
        if not check_equal:
            return False

    return True

def safe_repr(obj, limit=1000):
    """ Find the repr of the object, but limit the number of characters.
    """
    r = repr(obj)
    if len(r) > limit:
        hlimit = limit // 2
        r = '%s ... %s' % (r[:hlimit], r[-hlimit:])
    return r




### EOF ------------------------------------------------------------------------
