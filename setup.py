#!/usr/bin/env python
#
# Copyright (c) 2008-2010 by Enthought, Inc.
# All rights reserved.

"""
Code Analysis and Execution Tools

The CodeTools project includes packages that simplify meta-programming and
help the programmer separate data from code in Python. This library contains
classes that allow defining simple snippets, or "blocks", of Python code,
analyze variable dependencies in the code block, and use these dependencies to
construct or restrict an execution graph. These (restricted) code blocks can
then be executed in any namespace. However, this project also provides a
Traits-event-enhanced namespace, called a "context", which can be used in
place of a vanilla namespace to allow actions to be performed whenever
variables are assigned or retrieved from the namespace. This project is used
as the foundation for the BlockCanvas project.

Prerequisites
-------------
If you want to build CodeTools from source, you must first install
`setuptools <http://pypi.python.org/pypi/setuptools/0.6c8>`_.

"""

import traceback
import sys

from distutils import log
from distutils.command.build import build as distbuild
from setuptools import setup, find_packages
from setuptools.command.develop import develop


# FIXME: This works around a setuptools bug which gets setup_data.py metadata
# from incorrect packages. Ticket #1592
#from setup_data import INFO
setup_data = dict(__name__='', __file__='setup_data.py')
execfile('setup_data.py', setup_data)
INFO = setup_data['INFO']


# Pull the description values for the setup keywords from our file docstring.
DOCLINES = __doc__.split("\n")


# Make the actual setup call.
setup(
    author = 'Enthought, Inc.',
    author_email = 'info@enthought.com',
    download_url = ('http://www.enthought.com/repo/ETS/CodeTools-%s.tar.gz' %
                    INFO['version']),
    classifiers = [c.strip() for c in """\
        Development Status :: 5 - Production/Stable
        Intended Audience :: Developers
        Intended Audience :: Science/Research
        License :: OSI Approved :: BSD License
        Operating System :: MacOS
        Operating System :: Microsoft :: Windows
        Operating System :: OS Independent
        Operating System :: POSIX
        Operating System :: Unix
        Programming Language :: Python
        Topic :: Scientific/Engineering
        Topic :: Software Development
        Topic :: Software Development :: Libraries
        """.splitlines() if len(c.strip()) > 0],
    description = DOCLINES[1],
    extras_require = INFO['extras_require'],
    include_package_data = True,
    install_requires = INFO['install_requires'],
    license = 'BSD',
    long_description = '\n'.join(DOCLINES[3:]),
    maintainer = 'ETS Developers',
    maintainer_email = 'enthought-dev@enthought.com',
    name = 'CodeTools',
    namespace_packages = [
        "enthought",
        ],
    packages = find_packages(),
    platforms = ["Windows", "Linux", "Mac OS-X", "Unix", "Solaris"],
    tests_require = [
        'nose >= 0.10.3',
        ],
    test_suite = 'nose.collector',
    url = 'http://code.enthought.com/projects/code_tools.php',
    version = INFO['version'],
    zip_safe = False,
    )

