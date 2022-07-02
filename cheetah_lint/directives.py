from __future__ import annotations

import functools

import lxml.etree
from refactorlib.node import ExactlyOneError

from cheetah_lint.imports import CheetahImport


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
        return xmldoc.xpath_one(f'./Directive[starts-with(., "{directive}")]')
    except ExactlyOneError:
        return None


get_extends_directive = functools.partial(
    _get_special_directive, directive='#extends',
)
get_implements_directive = functools.partial(
    _get_special_directive, directive='#implements',
)


def _get_imports(xmldoc: lxml.etree.Element, name: str) -> list[CheetahImport]:
    xml_elements = xmldoc.xpath(
        f'./Directive['
        f'    SimpleExprDirective/UnbracedExpression/Py[1]['
        f"        text() = '{name}'"
        f'    ]'
        f']',
    )
    return [CheetahImport(xml_element) for xml_element in xml_elements]


def get_all_imports(xmldoc: lxml.etree.Element) -> list[CheetahImport]:
    return [*_get_imports(xmldoc, 'import'), *_get_imports(xmldoc, 'from')]
