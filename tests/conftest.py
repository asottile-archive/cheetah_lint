# -*- coding: utf-8 -*-
import pytest

from cheetah_lint import five


@pytest.fixture(autouse=True)
def no_warnings(recwarn):
    yield
    warnings = tuple(
        '{}:{} {}'.format(warning.filename, warning.lineno, warning.message)
        for warning in recwarn
        # cheetah raises this warning when compiling a trivial file
        if not (
            isinstance(warning.message, UserWarning) and
            five.text(warning.message) == (
                'You supplied an empty string for the source!'
            )
        )
    )
    assert not warnings
