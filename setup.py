#!/usr/bin/env python

import sys
import os
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.version_info < (2,5):
    raise NotImplementedError("Sorry, you need at least Python 2.5 or Python 3.x to use udprecv.")

import udprecv

setup(name='udprecv',
    version=udprecv.__version__,
    description = udprecv.__doc__.splitlines()[0],
    author=udprecv.__author__,
    author_email='joao.taveira@gmail.com',
    url='https://github.com/jta/udprecv',
    py_modules=['udprecv'],
    scripts=['udprecv.py'],
    license='MIT',
    platforms = 'any',
    classifiers=['Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        ],
)
