# coding: utf-8

from setuptools import setup

setup(
    name = 'homekeeper',
    packages = ['homekeeper'],
    version = "0.1",
    license = "LGPLv3+",
    author = "João S. O. Bueno",
    author_email = "gwidion@gmail.com",
    description = "short house-keeping tetrizoid for 2019 global game jam",
    keywords = "game gamejam pygame",
    py_modules = ['homekeeper'],
    url = 'https://github.com/jsbueno/homekeeper',
    long_description = '', # open('README.md').read(),
    test_requires = ['pytest'],
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ]
)
