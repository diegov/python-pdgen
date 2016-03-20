#!/usr/bin/env python

from setuptools import setup

setup(name='PdGen',
      version='0.1',
      description='Python tools to generate PureData patches',
      author='Diego Veralli',
      url='https://github.com/diegov/python-pdgen',
      packages=['pdgen'],
      extras_require={'validation': ['pylibpd']},
      install_requires=['networkx', 'pygraphviz'],
     )
