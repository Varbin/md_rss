"""
Installation script of md_tools.

Usage (pip):
    pip install .

Usage (direct):
    setup.py build  # "Build" + Checkup
    setup.py install  # Installation
"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
    print("Warning: setuptools not found! Falling back to raw distutils.")
    print(" -> This may not properly register packages with python.")
    print(" -> Script installation not available.")
    print("")

import re

with open('md_tools/__init__.py') as malshare_db:
    code = malshare_db.read()

metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", code))
description = 'Tools for adding dynamic content to static markdown based websites'

setup(
    name='md_tools',
    version=metadata.get('version'),

    author=metadata.get('author'),
    author_email=metadata.get('email'),
    license=metadata.get('license'),
    url='https://github.com',
    description=description,
    packages=['md_tools'],
    install_requires=['python-dateutil', 'PyRSS2Gen', 'beautifulsoup4', 'markdown', 'feedparser'],

    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ]
)
