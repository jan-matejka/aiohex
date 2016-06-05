#! /usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import aiohex

setup(
  name         = 'aiohex'
, version      = aiohex.__version__
, description  = 'aiohttp example'
, author       = 'Jan Matějka'
, author_email = 'yac@blesmrt.net'
# ,  url=''

, packages = find_packages(
    where = '.'
  )

, install_requires = [
    "setuptools"
  , "aiohttp"
  , "aiopg"
  , "sqlalchemy"
  , "networkx"
  , "numpy"
  ]

, tests_require = [
    "pytest"
  , "nose"
  , "cram"
  # zsh
  ]

, entry_points = {
    'console_scripts': ['aiohex = aiohex:main']
  }

, classifiers = [
    "Programming Language :: Python :: 3 :: Only"
  , "Programming Language :: Python :: 3.5"
  ]
)

