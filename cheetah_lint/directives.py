# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import functools

from refactorlib.node import ExactlyOneError

from cheetah_lint.imports import CheetahFromImport
from cheetah_lint.imports import CheetahImportImport


def get_compiler_settings_directive(xmldoc):
    try:
        return xmldoc.xpath_one('./compiler-settings')
    except ExactlyOneError:
        return None


def _get_special_directive(xmldoc, directive):
    try:
        return xmldoc.xpath_one(
            './Directive[starts-with(., "{}")]'.format(directive)
        )
    except ExactlyOneError:
        return None


get_extends_directive = functools.partial(
    _get_special_directive, directive='#extends',
)
get_implements_directive = functools.partial(
    _get_special_directive, directive='#implements',
)


def _get_import_helper(xmldoc, directive_cls):
    xml_elements = xmldoc.xpath(
        './Directive['
        '    SimpleExprDirective/UnbracedExpression/Py[1]['
        "        text() = '{}'"
        '    ]'
        ']'.format(
            directive_cls.IMPORT_NAME,
        )
    )
    return [directive_cls(xml_element) for xml_element in xml_elements]


get_from_imports = functools.partial(
    _get_import_helper, directive_cls=CheetahFromImport,
)
get_import_imports = functools.partial(
    _get_import_helper, directive_cls=CheetahImportImport,
)


def get_all_imports(xmldoc):
    return get_import_imports(xmldoc) + get_from_imports(xmldoc)
