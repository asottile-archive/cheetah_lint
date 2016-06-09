# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup


setup(
    name='cheetah_lint',
    description='Linting tools for the Cheetah templating language.',
    url='https://github.com/asottile/cheetah_lint',
    version='0.2.2',
    author='Anthony Sottile',
    author_email='asottile@umich.edu',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    packages=find_packages('.', exclude=('tests*', 'testing*')),
    install_requires=[
        'aspy.refactor_imports>=0.2.1',
        'cached-property',
        'flake8',
        'refactorlib[cheetah]>=0.12.0,<=0.12.999',
        'yelp-cheetah>=0.16.1,<=0.16.999',
    ],
    entry_points={
        'console_scripts': [
            'cheetah-reorder-imports = cheetah_lint.reorder_imports:main',
            'cheetah-flake = cheetah_lint.flake:main',
        ],
    },
)
