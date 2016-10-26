# -*- coding: utf-8 -*-
import pytest

from cheetah_lint import five


@pytest.yield_fixture(autouse=True)
def no_warnings(recwarn):
    yield
    ret = len(tuple(
        warning for warning in recwarn
        # cheetah raises this warning when compiling a trivial file
        if not (
            isinstance(warning.message, UserWarning) and
            five.text(warning.message) == (
                'You supplied an empty string for the source!'
            )
        )
    ))
    assert ret == 0
