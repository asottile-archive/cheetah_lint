# -*- coding: utf-8 -*-
import pytest

from cheetah_lint import five


@pytest.yield_fixture(autouse=True)
def no_lxml_warnings(recwarn):
    yield
    for warning in recwarn:
        assert five.text(warning.message) != (
            'The behavior of this method will change in future versions. '
            "Use specific 'len(elem)' or 'elem is not None' test instead."
        )
