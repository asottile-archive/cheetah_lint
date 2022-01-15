from __future__ import annotations

import functools
from typing import TypeVar

import lxml.etree
from refactorlib.node import ExactlyOneError

from cheetah_lint.imports import CheetahFromImport
from cheetah_lint.imports import CheetahImport
from cheetah_lint.imports import CheetahImportImport

T = TypeVar('T', bound=CheetahImport)


def get_compiler_settings_directive(
        xmldoc: lxml.etree.Element,
) -> lxml.etree.Element | None:
    try:
        return xmldoc.xpath_one('./compiler-settings')
    except ExactlyOneError:
        return None


def _get_special_directive(
        xmldoc: lxml.etree.Element,
        directive: str,
) -> lxml.etree.Element | None:
    try:
        return xmldoc.xpath_one(
            f'./Directive[starts-with(., "{directive}")]',
        )
    except ExactlyOneError:
        return None


get_extends_directive = functools.partial(
    _get_special_directive, directive='#extends',
)
get_implements_directive = functools.partial(
    _get_special_directive, directive='#implements',
)


def _get_import_helper(
        xmldoc: lxml.etree.Element,
        directive_cls: type[T],
) -> list[T]:
    xml_elements = xmldoc.xpath(
        './Directive['
        '    SimpleExprDirective/UnbracedExpression/Py[1]['
        "        text() = '{}'"
        '    ]'
        ']'.format(
            directive_cls.IMPORT_NAME,
        ),
    )
    return [directive_cls(xml_element) for xml_element in xml_elements]


def get_from_imports(xmldoc: lxml.etree.Element) -> list[CheetahFromImport]:
    return _get_import_helper(xmldoc, CheetahFromImport)


def get_import_imports(
        xmldoc: lxml.etree.Element,
) -> list[CheetahImportImport]:
    return _get_import_helper(xmldoc, CheetahImportImport)


def get_all_imports(xmldoc: lxml.etree.Element) -> list[CheetahImport]:
    return [*get_import_imports(xmldoc), *get_from_imports(xmldoc)]
