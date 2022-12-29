[![build status](https://github.com/asottile/cheetah_lint/actions/workflows/main.yml/badge.svg)](https://github.com/asottile/cheetah_lint/actions/workflows/main.yml)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/asottile/cheetah_lint/main.svg)](https://results.pre-commit.ci/latest/github/asottile/cheetah_lint/main)

cheetah_lint
============

Linting tools for the [yelp_cheetah](https://github.com/Yelp/yelp_cheetah) templating language.


## Installation

```bash
pip install cheetah-lint
```


## Console scripts

```console
$ cheetah-reorder-imports --help
usage: cheetah-reorder-imports [-h] [filenames [filenames ...]]

positional arguments:
  filenames

optional arguments:
  -h, --help  show this help message and exit
```

```console
$ cheetah-flake --help
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
