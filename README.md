[![Build Status](https://dev.azure.com/asottile/asottile/_apis/build/status/asottile.cheetah_lint?branchName=master)](https://dev.azure.com/asottile/asottile/_build/latest?definitionId=41&branchName=master)
[![Azure DevOps coverage](https://img.shields.io/azure-devops/coverage/asottile/asottile/41/master.svg)](https://dev.azure.com/asottile/asottile/_build/latest?definitionId=41&branchName=master)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/asottile/cheetah_lint/master.svg)](https://results.pre-commit.ci/latest/github/asottile/cheetah_lint/master)

cheetah_lint
============

Linting tools for the [yelp_cheetah](https://github.com/Yelp/yelp_cheetah) templating language.


## Installation

`pip install cheetah-lint`


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
