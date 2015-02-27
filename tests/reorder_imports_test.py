from __future__ import unicode_literals

import io
import os
import os.path

import pytest

from cheetah_lint.reorder_imports import main
from cheetah_lint.reorder_imports import perform_step
from cheetah_lint.reorder_imports import STEPS


INPUT_DIRECTORY = 'tests/inputs'
OUTPUT_DIRECTORY = 'tests/outputs'


TESTS = tuple(
    template for template in os.listdir(INPUT_DIRECTORY)
    if not template.startswith('_')
)


def get_input_output(template):
    return tuple(
        io.open(os.path.join(base, template)).read()
        for base in (INPUT_DIRECTORY, OUTPUT_DIRECTORY)
    )


@pytest.mark.parametrize('template', TESTS)
def test_integration_template(template):
    contents, expected = get_input_output(template)
    for step in STEPS:
        contents = perform_step(contents, step)
    assert expected == contents


@pytest.mark.parametrize('template', TESTS)
def test_integration_calls_main(tmpdir, template):
    contents, expected = get_input_output(template)
    template_path = os.path.join(tmpdir.strpath, 'tmp.tmpl')

    with io.open(template_path, 'w') as template_file:
        template_file.write(contents)

    main([template_path])

    end_contents = io.open(template_path).read()
    assert expected == end_contents
