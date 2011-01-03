"""
Installer for scunch.
"""
from setuptools import setup, find_packages

from scunch import scunch

setup(
    name="scunch",
    version=scunch.__version__,
    packages=["scunch"],
    description="copy folder over working copy and apply add/remove/modify (svn)",
    entry_points = {
        'console_scripts': [
            'scunch = scunch.scunch:main'
        ],
    },
    test_suite = "scunch.test_scunch",
    keywords="svn scm version import apply copy transfer punch working work copy",
    author="Thomas Aglassinger",
    author_email="roskakori@users.sourceforge.net",
    url="http://pypi.python.org/pypi/scunch/",
    license="GNU Library or Lesser General Public License (LGPL)",
    long_description=scunch.__doc__, #@UndefinedVariable
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Topic :: Software Development :: Version Control",
    ],
)
