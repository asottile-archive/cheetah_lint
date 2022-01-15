from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def no_warnings(recwarn):
    yield
    warnings = tuple(
        f'{warning.filename}:{warning.lineno} {warning.message}'
        for warning in recwarn
        # cheetah raises this warning when compiling a trivial file
        if not (
            isinstance(warning.message, UserWarning) and
            str(warning.message) == (
                'You supplied an empty string for the source!'
            )
        )
    )
    assert not warnings
