# Copyright (c) 2008-2011 by Enthought, Inc.
# All rights reserved.

from setuptools import setup, find_packages


# This works around a setuptools bug which gets setup_data.py metadata
# from incorrect packages.
setup_data = dict(__name__='', __file__='setup_data.py')
execfile('setup_data.py', setup_data)
INFO = setup_data['INFO']


setup(
    author = 'Enthought, Inc.',
    author_email = 'info@enthought.com',
    download_url = ('http://www.enthought.com/repo/ets/CodeTools-%s.tar.gz' %
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
    description = 'code analysis and execution tools',
    long_description = open('README.rst').read(),
    include_package_data = True,
    package_data = {'codetools': ['contexts/images/*.png']},
    install_requires = INFO['install_requires'],
    license = 'BSD',
    maintainer = 'ETS Developers',
    maintainer_email = 'enthought-dev@enthought.com',
    name = 'CodeTools',
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
