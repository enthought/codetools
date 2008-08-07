# Function to convert simple ETS project names and versions to a requirements
# spec that works for both development builds and stable builds.  Allows
# a caller to specify a max version, which is intended to work along with
# Enthought's standard versioning scheme -- see the following write up:
#    https://svn.enthought.com/enthought/wiki/EnthoughtVersionNumbers
def etsdep(p, min, max=None, literal=False):
    require = '%s >=%s.dev' % (p, min)
    if max is not None:
        if literal is False:
            require = '%s, <%s.a' % (require, max)
        else:
            require = '%s, <%s' % (require, max)
    return require

# Delcare our ETS project dependencies.
TRAITS = etsdep('Traits', '3.0.1')


# A dictionary of the setup data information.
INFO = {
    'install_requires' : [
        TRAITS,
        ],
    'name': 'CodeTools',
    'version': '3.0.0',
    }
