"""
Installer for scunch.

Developer cheat sheet
---------------------

Create the installer archive::

  $ python setup.py sdist --formats=zip

Upload release to PyPI::

  $ python setup.py test
  $ python setup.py sdist --formats=zip upload

Tag a release::

  $ git tag -a -m "Tagged version 0.x.y." 0.x.y
  $ git push --tags
"""
# Copyright (C) 2011 Thomas Aglassinger
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from setuptools import setup, find_packages

from scunch import scunch

setup(
    name="scunch",
    version=scunch.__version__,
    packages=["scunch"],
    description="Update svn working copy from folder.",
    install_requires=[
        "nose>=1.0"
    ],
    entry_points={
        'console_scripts': [
            'scunch = scunch.scunch:main'
        ],
    },
    test_suite="nose.collector",
    keywords="svn scm version import apply copy transfer punch working work",
    author="Thomas Aglassinger",
    author_email="roskakori@users.sourceforge.net",
    url="http://pypi.python.org/pypi/scunch/",
    license="GNU Library or Lesser General Public License (LGPL)",
    long_description=scunch.__doc__,  # @UndefinedVariable
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Version Control",
    ],
)
