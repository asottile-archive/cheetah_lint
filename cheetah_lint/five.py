# -*- coding: utf-8 -*-
# pylint:disable=undefined-variable
"""five: six, redux"""

PY2 = (str is bytes)
PY3 = (str is not bytes)

# provide a symettrical `text` type to `bytes`
if PY2:  # pragma: no cover
    text = unicode  # flake8: noqa

    def n(s):
        if isinstance(s, bytes):
            return s
        else:
            return s.encode('UTF-8')
else:  # pragma: no cover
    text = str

    def n(s):
        if isinstance(s, text):
            return s
        else:
            return s.decode('UTF-8')
