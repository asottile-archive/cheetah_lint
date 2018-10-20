# -*- coding: utf-8 -*-
"""five: six, redux"""

PY2 = (str is bytes)
PY3 = (str is not bytes)

# provide a symettrical `text` type to `bytes`
if PY2:  # pragma: no cover
    text = unicode  # noqa

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
