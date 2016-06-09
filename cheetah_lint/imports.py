# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import lxml.etree
from aspy.refactor_imports.import_obj import FromImport
from aspy.refactor_imports.import_obj import ImportImport
from cached_property import cached_property


def combine_import_objs(import_objs):
    return ''.join('#' + import_obj.to_text() for import_obj in import_objs)


class CheetahImport(object):
    IMPORT_NAME = NotImplemented
    IMPORT_TYPE = NotImplemented

    def __init__(self, directive_element):
        self.directive_element = directive_element

    @cached_property
    def import_obj(self):
        expr = self.directive_element.xpath_one(
            'descendant::UnbracedExpression',
        ).totext(encoding='unicode')
        return self.IMPORT_TYPE.from_str(expr)

    def get_new_import_statements(self):
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
