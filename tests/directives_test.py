# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

from refactorlib.cheetah.parse import parse

from cheetah_lint.directives import get_compiler_settings_directive
from cheetah_lint.directives import get_extends_directive
from cheetah_lint.directives import get_from_imports
from cheetah_lint.directives import get_implements_directive
from cheetah_lint.directives import get_import_imports


def get_parsed_doc():
    doc = (
        '#compiler-settings\n'
        'useLegacyImportMode = True\n'
        '#end compiler-settings\n'
        '#extends templates.base\n'
        '#implements respond\n'
        '\n'
        '#import itertools\n'
        '#import yelp.util.helpers.template as h\n'
        '#from foo.bar import baz\n'
        '#from a import b as c\n'
    )
    return parse(doc)


def test_get_compiler_settings_directive():
    ret = get_compiler_settings_directive(get_parsed_doc())
    assert ret.totext(encoding='unicode') == (
        '#compiler-settings\n'
        'useLegacyImportMode = True\n'
        '#end compiler-settings\n'
    )


def test_get_extends_directive():
    ret = get_extends_directive(get_parsed_doc())
    assert ret.totext(encoding='unicode') == '#extends templates.base\n'


def test_get_implements_directive():
    ret = get_implements_directive(get_parsed_doc())
    assert ret.totext(encoding='unicode') == '#implements respond\n'


def test_get_from_imports():
    ret = get_from_imports(get_parsed_doc())
    to_texts = [el.directive_element.totext(encoding='unicode') for el in ret]
    assert to_texts == [
        '#from foo.bar import baz\n',
        '#from a import b as c\n'
    ]


def test_get_import_imports():
    ret = get_import_imports(get_parsed_doc())
    to_texts = [el.directive_element.totext(encoding='unicode') for el in ret]
    assert to_texts == [
        '#import itertools\n',
        '#import yelp.util.helpers.template as h\n',
    ]
