from __future__ import absolute_import
from __future__ import unicode_literals

import functools

from refactorlib.node import ExactlyOneError

from cheetah_lint.imports import CheetahFromImport
from cheetah_lint.imports import CheetahImportImport


def _get_special_directive(xmldoc, element):
    try:
        return xmldoc.xpath_one('//cheetah/Directive[{0}]'.format(element))
    except ExactlyOneError:
        return None


get_compiler_settings_directive = functools.partial(
    _get_special_directive, element='CompilerSettings',
)
get_extends_directive = functools.partial(
    _get_special_directive, element='Extends',
)
get_implements_directive = functools.partial(
    _get_special_directive, element='Implements',
)


def _get_import_helper(xmldoc, directive_cls):
    xml_elements = xmldoc.xpath(
        '//cheetah/Directive['
        '    SimpleExprDirective/Expression/ExpressionParts/Py[1]['
        "        text() = '{0}'"
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
