# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import pytest

from cheetah_lint import five
from cheetah_lint.flake import _find_bounds
from cheetah_lint.flake import _get_line_no_from_comments
from cheetah_lint.flake import filter_known_unused_assignments
from cheetah_lint.flake import filter_known_unused_imports
from cheetah_lint.flake import get_flakes
from cheetah_lint.flake import LINE_ERROR_MSG_RE
from cheetah_lint.flake import LINECOL_COMMENT_RE
from cheetah_lint.flake import main
from cheetah_lint.flake import PY_DEF_RE
from cheetah_lint.flake import STRIP_SYMBOLS_RE


def test_filter_known_unused_imports_filters_known():
    ret = filter_known_unused_imports(
        ((1, "F401 'VFFSL' imported but unused"),)
    )
    assert ret == ()


def test_filter_known_unused_imports_ignores_unknown():
    ret = filter_known_unused_imports(((1, "F401 'a' imported but unused"),))
    assert ret == ((1, "F401 'a' imported but unused"),)


def test_filter_known_unused_assignments_filters_known():
    ret = filter_known_unused_assignments((
        (1, "F841 local variable '_dummyTrans' is assigned to but never used"),
    ))
    assert ret == ()


def test_filter_known_unused_assignments_ignores_unknown():
    ret = filter_known_unused_assignments((
        (1, "F841 local variable 'a' is assigned to but never used"),
    ))
    assert ret == (
        (1, "F841 local variable 'a' is assigned to but never used"),
    )


def test_linecol_comment_regex_no_match():
    assert LINECOL_COMMENT_RE.match(
        "            write('''                ''')\n"
    ) is None


def test_linecol_comment_regex_match():
    assert LINECOL_COMMENT_RE.match(
        '        if meta_robots.should_display: '
        '# generated from line 260, col 13\n'
    ).group(1) == '260'


def test_linecol_comment_regex_other_match():
    assert LINECOL_COMMENT_RE.match(
        "        _v = bar # u'$bar' on line 1, col 1\n"
    ).group(1) == '1'


def test_line_error_message_no_match():
    assert LINE_ERROR_MSG_RE.match("F401 'module' imported but unused") is None


@pytest.mark.parametrize(
    'line',
    (
        "F401 import 'module' from line 9001 shadowed by loop variable",
        "F403 redefinition of unused 'name' from line 9001",
        "F811 list comprehension redefineds 'name' from line 9001",
    ),
)
def test_line_error_message_match(line):
    assert LINE_ERROR_MSG_RE.match(line).group(2) == '9001'


def test_line_error_message_sub():
    assert LINE_ERROR_MSG_RE.sub(
        r'\g<1>5',
        "F401 import 'module' from line 9001 shadowed by loop variable",
    ) == (
        "F401 import 'module' from line 5 shadowed by loop variable"
    )


@pytest.mark.parametrize(
    'input_str',
    (
        ('    def foo(self, **KWS):\n'),
        ('    def foo(self, foo=bar, **KWS):\n'),
        ('    def foo(self, foo, **KWS):\n'),
        ('    def foo(self, foo, **kwargs):\n'),
    ),
)
def test_py_def_re_matches(input_str):
    assert PY_DEF_RE.match(input_str) is not None


def test_py_def_re_specific_matches():
    match = PY_DEF_RE.match('    def foo(self):\n')
    assert match.group(1) == 'def foo('
    assert match.group(2) == ''
    assert match.group(3) == '):'


def test_py_def_re_specific_matches_with_params():
    match = PY_DEF_RE.match('    def foo(self, foo=bar):\n')
    assert match.group(1) == 'def foo('
    assert match.group(2) == 'foo=bar'
    assert match.group(3) == '):'


def test_py_def_re_specific_matches_with_kwargs():
    match = PY_DEF_RE.match('    def foo(self, foo=bar, **kwargs):\n')
    assert match.group(1) == 'def foo('
    assert match.group(2) == 'foo=bar, **kwargs'
    assert match.group(3) == '):'


@pytest.mark.parametrize(
    ('input_str', 'expected'),
    (
        ('    def foo(self):\n', 'def foo():\n'),
        ('    def foo(self, foo=bar):\n', 'def foo(foo=bar):\n'),
        (
            '    def foo(self, foo=bar, **kwargs):\n',
            'def foo(foo=bar, **kwargs):\n',
        ),
    ),
)
def test_py_def_replace(input_str, expected):
    assert PY_DEF_RE.sub(r'\1\2\3', input_str) == expected


@pytest.mark.parametrize(
    ('input_str', 'expected'),
    (
        ('foobar', 'foobar'),
        ('foo = bar', 'foobar'),
        ('from foo import bar', 'fromfooimportbar'),
        ('bar = $baz', 'barbaz'),
    ),
)
def test_strip_symbols_re(input_str, expected):
    assert STRIP_SYMBOLS_RE.sub('', input_str) == expected


@pytest.mark.parametrize(
    ('line', 'expected'),
    (
        ('x = 1 # generated from line 5, col 6', 5),
        ('hai', 0),
    ),
)
def test_get_line_no_from_comments(line, expected):
    assert _get_line_no_from_comments(line) == expected


CHEETAH_BY_LINE_NO = ('',) + tuple(
    '## line {0}'.format(i) for i in range(1, 9)
)


@pytest.mark.parametrize('py_line', (1, 2, 3, 4, 5))
def test_find_bounds_no_comments(py_line):
    py_by_line_no = (
        '',
        'a# line 1\n',
        'b# line 2\n',
        'c# line 3\n',
        'd# line 4\n',
        'e# line 5\n',
    )
    assert _find_bounds(py_line, py_by_line_no, CHEETAH_BY_LINE_NO) == (0, 9)


@pytest.mark.parametrize('py_line', (2, 3, 4))
def test_find_bounds_comment_above_none_below(py_line):
    py_by_line_no = (
        '',
        '1# line 1 # generated from line 2, col 5\n',
        '2# line 2\n',
        '3# line 3\n',
        '4# line 4\n',
    )
    assert _find_bounds(py_line, py_by_line_no, CHEETAH_BY_LINE_NO) == (2, 9)


@pytest.mark.parametrize('py_line', (1, 2, 3))
def test_find_bounds_comment_below_not_above(py_line):
    py_by_line_no = (
        '',
        'a# line 1\n',
        'b# line 2\n',
        'c# line 3\n',
        'd# line 4 # generated from line 6, col 5\n',
    )
    assert _find_bounds(py_line, py_by_line_no, CHEETAH_BY_LINE_NO) == (0, 7)


@pytest.mark.parametrize('py_line', (2, 3))
def test_find_bounds_above_and_below(py_line):
    py_by_line_no = (
        '',
        '1# line 1 # generated from line 2, col 6\n',
        '2# line 2\n',
        '3# line 3\n',
        '4# line 4 # generated from line 6, col 5\n',
    )
    assert _find_bounds(py_line, py_by_line_no, CHEETAH_BY_LINE_NO) == (2, 7)


def test_get_flakes_trivial():
    assert get_flakes('') == ((1, 'T005 File is empty'),)


def test_with_extends():
    assert get_flakes('#extends templates.base\n') == ()


def test_prints_a_variable():
    assert get_flakes('$foo $bar $baz') == ()


def test_really_really_long_line():
    assert get_flakes('a' * 9001) == ()


def test_multi_line_invocation():
    assert get_flakes(
        '$foo(\n'
        '    $bar,\n'
        ')'
    ) == ()


def test_other_multi_line_invocation():
    assert get_flakes(
        '$foo("bar"\n'
        '    "baz"\n'
        ')'
    ) == ()


def test_indented_thrice_multiline():
    assert get_flakes(
        '#def foo()\n'
        '    <div>\n'
        '        <div>\n'
        '            $bar(\n'
        '                $baz,\n'
        '            )\n'
        '        </div>\n'
        '    </div>\n'
        '#end def\n'
    ) == ()


def test_multiline_dictionary_literal():
    assert get_flakes(
        '#py foo = {\n'
        '    "bar": "baz",\n'
        '}\n'
        '$foo\n'
    ) == ()


def test_indented_multiline_dictionary_literal():
    assert get_flakes(
        '#if True\n'
        '    #py foo = {\n'
        '        "bar": "baz",\n'
        '    }\n'
        '    $foo\n'
        '#end if\n'
    ) == ()


def test_oneline_directive_followed_by_directive():
    assert get_flakes(
        '#if True\n'
        '    #def title()##end def#\n'
        '    #py foo = "bar"\n'
        '    $foo\n'
        '#end if\n'
    ) == ()


def test_module_imported_but_unused():
    assert get_flakes('#import foo') == (
        (1, "F401 'foo' imported but unused"),
    )


def test_module_imported_but_unused_lots_of_lines():
    assert get_flakes(
        '#import foo\n'
        '#def womp()\n'
        '    $bar\n'
        '#end def\n'
    ) == (
        (1, "F401 'foo' imported but unused"),
    )


def test_module_shadowed_by_loop_variable():
    assert get_flakes(
        '#import foo\n'
        '\n'
        '$foo\n'
        '#for foo in (1, 2, 3)\n'
        '    $foo\n'
        '#end for\n'
    ) == (
        (4, "F402 import 'foo' from line 1 shadowed by loop variable"),
    )


def test_star_import():
    assert get_flakes('#from foo import *') == (
        (1, "F403 'from foo import *' used; unable to detect undefined names"),
    )


def test_redefinition_of_unused_name():
    assert get_flakes(
        '#import foo.bar\n'
        '#import foo.bar\n'
        '$foo.baz()'
    ) == (
        (2, "F811 redefinition of unused 'foo' from line 1"),
    )


def test_redefinition_of_unused_name_block_def():
    assert get_flakes(
        '#block foo\n'
        '#end block\n'
        '#def foo()\n'
        '#end def\n'
    ) == (
        (3, "F811 redefinition of unused 'foo' from line 1"),
    )


def test_list_comprehension_redefines_name():
    # python 3 makes this not an issue
    expected = (
        ((1, "F841 local variable 'foo' is assigned to but never used"),)
        if five.PY3 else
        ((2, "F812 list comprehension redefines 'foo' from line 1"),)
    )
    assert get_flakes(
        '#py foo = $bar\n'
        '#for bar in [foo for foo in (1, 2, 3)]\n'
        '    $bar\n'
        '#end for\n'
    ) == expected


def test_unused_local_variable():
    assert get_flakes('#py foo = $bar') == (
        (1, "F841 local variable 'foo' is assigned to but never used"),
    )


def test_comparison_to_none():
    assert get_flakes('#if $foo == None: herp') == (
        (1, "E711 comparison to None should be 'if cond is None:'"),
    )


def test_comparison_to_true():
    assert get_flakes('#if $foo == True: herp') == (
        (
            1,
            "E712 comparison to True should be "
            "'if cond is True:' or 'if cond:'",
        ),
    )


def test_membership():
    assert get_flakes('#if not $baz in $foo: herp') == (
        (1, "E713 test for membership should be 'not in'"),
    )


def test_identity():
    assert get_flakes('#if not $bar is $foo: herp') == (
        (1, "E714 test for object identity should be 'is not'"),
    )


def test_has_key():
    assert get_flakes('#if $foo.has_key($bar): herp') == (
        (1, "W601 .has_key() is deprecated, use 'in'"),
    )


def test_syntaxerror():
    assert get_flakes('#if foo = "bar": herp') == (
        (1, "E901 SyntaxError: invalid syntax"),
    )


def test_context_manager():
    assert get_flakes(
        '#import contextlib\n'
        '#@contextlib.contextmanager\n'
        '#def foo()\n'
        '    before\n'
        '    #yield\n'
        '    after\n'
        '#end def\n'
    ) == ()


def test_cannot_determine_line_number():
    assert get_flakes(
        '$foo(\n'
        '    $bar == True,\n'
        ')'
    ) == (
        (
            0,
            "E712 comparison to True should be "
            "'if cond is True:' or 'if cond:'"
        ),
    )


def test_implements_respond_no_extend():
    assert get_flakes('#implements respond') == (
        (1, "T001 '#implements respond' is assumed without '#extends'"),
    )


def test_implements_respond_with_extend():
    assert get_flakes('#extends foo\n#implements respond') == ()


def test_implements_non_respond():
    assert get_flakes('#implements foo') == ()


def test_extends_cheetah_template():
    assert get_flakes('#extends Cheetah.Template') == (
        (1, "T002 '#extends Cheetah.Template' is assumed without '#extends'"),
    )


def test_extends_something_else():
    assert get_flakes('#extends foo') == ()


def test_indents_with_tabs():
    assert get_flakes(
        '#if True:\n'
        '\tHello world\n'
        '#end if\n',
    ) == (
        (2, 'T003 Indentation contains tabs'),
    )


def test_indents_not_four_spaces():
    assert get_flakes(
        '#if True:\n'
        '   Hello world\n'
        '#end if\n'
    ) == (
        (2, 'T004 Indentation is not a multiple of 4'),
    )


def test_unicode_literals():
    assert get_flakes(
        "$_(u'hi ☃')",
    ) == (
        (
            1,
            'P001 unicode literal prefix is unnecessary (assumed) in cheetah '
            "templates: u'hi ☃'"
        ),
    )


def test_main_integration(tmpdir):
    good_file = tmpdir.join('good.tmpl')
    good_file.write('Hello world')
    assert main([good_file.strpath]) == 0


def test_main_integration_fail(tmpdir):
    bad_file = tmpdir.join('bad.tmpl')
    bad_file.write('#import foo')
    assert main([bad_file.strpath]) == 1


def test_compiler_settings():
    assert get_flakes(
        '#compiler-settings#useLegacyImportMode = True#end compiler-settings#',
    ) == ()
