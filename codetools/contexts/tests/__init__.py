from traits.api import push_exception_handler, pop_exception_handler

# Package-level setup and teardown.
def setup_package():
    push_exception_handler(handler=lambda *args, **kwds: None, reraise_exceptions=True)

def teardown_package():
    pop_exception_handler
