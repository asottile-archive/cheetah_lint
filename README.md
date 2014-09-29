[![Build Status](https://travis-ci.org/asottile/cheetah_lint.svg?branch=master)](https://travis-ci.org/asottile/cheetah_lint)
[![Coverage Status](https://img.shields.io/coveralls/asottile/cheetah_lint.svg?branch=master)](https://coveralls.io/r/asottile/cheetah_lint)

cheetah_lint
==========

Linting tools for the [yelp_cheetah](https://github.com/Yelp/yelp_cheetah) templating language.


## Installation

`pip install cheetah-lint`


## Console scripts

```
cheetah-reorder-imports --help
usage: cheetah-reorder-imports [-h] [filenames [filenames ...]]

positional arguments:
  filenames

optional arguments:
  -h, --help  show this help message and exit
```

```
cheetah-flake --help
usage: cheetah-flake [-h] [filenames [filenames ...]]

positional arguments:
  filenames   Filenames to flake.

optional arguments:
  -h, --help  show this help message and exit
```

## As a pre-commit hook

See [pre-commit](https://github.com/pre-commit/pre-commit) for instructions

Hooks available:
- `cheetah-reorder-imports` - This hook reorders imports in cheetah files.
- `cheetah-flake` - Lint cheetah code using flake8 and some other checks.
