from __future__ import annotations

import lxml.etree
from aspy.refactor_imports.import_obj import AbstractImportObj
from aspy.refactor_imports.import_obj import FromImport
from aspy.refactor_imports.import_obj import ImportImport
from cached_property import cached_property


def combine_import_objs(import_objs: AbstractImportObj) -> str:
    return ''.join('#' + import_obj.to_text() for import_obj in import_objs)


class CheetahImport:
    IMPORT_NAME: str
    IMPORT_TYPE: type[AbstractImportObj]

    def __init__(self, directive_element: lxml.etree.Element) -> None:
        self.directive_element = directive_element

    @cached_property
    def import_obj(self) -> AbstractImportObj:
        expr = self.directive_element.xpath_one(
            'descendant::UnbracedExpression',
        ).totext(encoding='unicode')
        return self.IMPORT_TYPE.from_str(expr)

    def get_new_import_statements(self) -> lxml.etree.Element:
        assert self.import_obj.has_multiple_imports
        ret = lxml.etree.Element('Imports')
        ret.text = combine_import_objs(self.import_obj.split_imports())
        return ret


class CheetahFromImport(CheetahImport):
    IMPORT_NAME = 'from'
    IMPORT_TYPE = FromImport


class CheetahImportImport(CheetahImport):
    IMPORT_NAME = 'import'
    IMPORT_TYPE = ImportImport
