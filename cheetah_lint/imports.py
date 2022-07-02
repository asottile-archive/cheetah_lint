from __future__ import annotations

import lxml.etree
from cached_property import cached_property
from classify_imports import Import
from classify_imports import import_obj_from_str
from classify_imports import ImportFrom


def combine_import_objs(import_objs: Import | ImportFrom) -> str:
    return ''.join(f'#{import_obj}' for import_obj in import_objs)


class CheetahImport:
    def __init__(self, directive_element: lxml.etree.Element) -> None:
        self.directive_element = directive_element

    @cached_property
    def import_obj(self) -> Import | ImportFrom:
        expr = self.directive_element.xpath_one(
            'descendant::UnbracedExpression',
        ).totext(encoding='unicode')
        return import_obj_from_str(expr)

    def get_new_import_statements(self) -> lxml.etree.Element:
        assert self.import_obj.is_multiple
        ret = lxml.etree.Element('Imports')
        ret.text = combine_import_objs(self.import_obj.split())
        return ret
