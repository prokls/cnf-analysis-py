#!/usr/bin/env python

"""
    cnfanalysis
    ~~~~~~~~~~~

    Analyze CNF files.

    .. code:: bash

        $ python3 setup.py cnfanalysis

    (C) 2015, meisterluk, BSD 3-clause license
"""

import os.path

from setuptools import setup


def readfile(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as fp:
        return fp.read()

setup(
    name='cnfanalysis',
    version='1.7.0',
    url='http://lukas-prokop.at/proj/cnfanalysis/',
    license='BSD',
    author='Lukas Prokop',
    author_email='admin@lukas-prokop.at',
    description='CNF file analysis',
    long_description=readfile('README.rst'),
    package_dir={'cnfanalysis': 'lib'},
    platforms='any',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Security :: Cryptography',
        'Topic :: Text Processing :: General'
    ],
    scripts=['bin/cnf-analysis-index.py', 'bin/cnf-analysis-inspect.py',
             'bin/cnf-analysis.py', 'bin/cnf-analysis-stats-annotate.py',
             'bin/cnf-analysis-stats-combine.py']
)
