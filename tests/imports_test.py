from __future__ import annotations

from refactorlib.cheetah.parse import parse

from cheetah_lint.directives import get_from_imports
from cheetah_lint.directives import get_import_imports


def import_import_from_string(s):
    return get_import_imports(parse(s))[0]


def from_import_from_string(s):
    return get_from_imports(parse(s))[0]


def test_not_has_multiple_imports():
    import_obj = from_import_from_string('#from foo import bar')
    assert import_obj.import_obj.has_multiple_imports is False


def test_has_multiple_imports():
    import_obj = from_import_from_string('#from foo import bar, baz')
    assert import_obj.import_obj.has_multiple_imports is True


def test_split_from_import():
    import_obj = from_import_from_string('#from foo import bar, baz as herp')
    ret = import_obj.get_new_import_statements()
    assert ret.text == '#from foo import bar\n#from foo import baz as herp\n'


def test_split_import_import():
    import_obj = import_import_from_string('#import foo, bar as baz')
    ret = import_obj.get_new_import_statements()
    assert ret.text == '#import foo\n#import bar as baz\n'
