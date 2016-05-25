# -*- coding: utf-8 -*-
# pylint:disable=undefined-variable
"""five: six, redux"""

PY2 = (str is bytes)
PY3 = (str is not bytes)

# provide a symettrical `text` type to `bytes`
if PY2:  # pragma: no cover
    text = unicode  # flake8: noqa
else:  # pragma: no cover
    text = str
