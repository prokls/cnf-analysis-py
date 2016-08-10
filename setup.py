#!/usr/bin/env python

"""
    cnfanalysis
    ~~~~~~~~~~~

    Analyze CNF files.

    .. code:: bash

        $ python3 setup.py install
        $ cnf-analysis-py triangle.cnf
        $ cat triangle.stats.json

    (C) 2015-2016, meisterluk, CC-0 license
"""

import os.path

from setuptools import setup


def readfile(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as fp:
        return fp.read()

setup(
    name='cnfanalysis',
    version='2.0.0',
    url='http://lukas-prokop.at/proj/cnf-analysis/',
    license='Public Domain',
    author='Lukas Prokop',
    author_email='admin@lukas-prokop.at',
    description='CNF file analysis',
    long_description=readfile('README.rst'),
    packages=['cnfanalysis'],
    platforms='any',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: Public Domain',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Security :: Cryptography',
        'Topic :: Text Processing :: General'
    ],
    entry_points={
        "console_scripts": [
            'cnf-analysis-py = cnfanalysis.scripts:main',
            'cnf-analysis-annotate = cnfanalysis.scripts:annotate'
        ]
    }
)
