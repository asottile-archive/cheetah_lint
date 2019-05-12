# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import re
import subprocess
import sys
import tempfile
import tokenize

from Cheetah.compile import compile_source
from Cheetah.legacy_compiler import LegacyCompiler

from cheetah_lint import five
from cheetah_lint.util import read_file


ACCEPTABLE_UNUSED_ASSIGNMENTS = ('_dummyTrans', 'NS')
UNUSED_ASSIGNMENTS_FLAKE8_MESSAGES = frozenset(
    "local variable '{}' is assigned to but never used".format(name)
    for name in ACCEPTABLE_UNUSED_ASSIGNMENTS
)

ACCEPTABLE_UNUSED_IMPORTS = (
    'Cheetah.NameMapper.value_from_namespace as VFNS',
)
UNUSED_IMPORTS_FLAKE8_MESSAGES = frozenset(
    "'{}' imported but unused".format(name)
    for name in ACCEPTABLE_UNUSED_IMPORTS
)


# The cheetah compiler produces problems with the following things given
# completely valid code:
# - Whitespace
# - undefined name 'name' - Variables referenced from the searchlist appear as
#   undefined variables when linting.
# Because of this, we select the errors we know to be actual problems
SELECTED_ERRORS = ','.join((
    # 'module' imported but unused
    'F401',
    # import 'module' from line N shadowed by loop variable
    'F402',
    # 'from module import *' used; unable to detect undefined names
    'F403',
    # dictionary key repeated with different values
    'F601', 'F602',
    # Use == / != to compare to literals
    'F632',
    # redefinition of unused 'name' from line N
    'F811',
    # list comprehension redefines 'name' from line N
    'F812',
    # local variable 'name' is assigned to but never used
    'F841',
    # comparison to None should be 'if cond is None:'
    'E711',
    # comparison to True should be 'if cond is True:' or 'if cond:'
    'E712',
    # test for membership should be 'not in'
    'E713',
    # test for object identity should be 'is not'
    'E714',
    # SyntaxError
    'E999',
    # .has_key() is deprecated, use 'in'
    'W601',
    # invalid escape sequence
    'W605',
))


class NoCompilerSettingsCompiler(LegacyCompiler):
    def add_compiler_settings(self):
        # Consume the settings string, but do not assign it
        self.clearStrConst()


def to_py(src):
    return compile_source(src, compiler_cls=NoCompilerSettingsCompiler)


def filter_known_errors(data):
    return tuple(
        (line, code, msg)
        for line, code, msg in data
        if not (code == 'F841' and msg in UNUSED_ASSIGNMENTS_FLAKE8_MESSAGES)
        if not (code == 'F401' and msg in UNUSED_IMPORTS_FLAKE8_MESSAGES)
    )


LINECOL_COMMENT_RE = re.compile(r'^.+#.+line (\d+), col \d+')
LINE_ERROR_MSG_RE = re.compile(r'^(.+from line )(\d+)')
PY_DEF_RE = re.compile(
    # A bit complicated, but gets these interesting bits from a function def:
    # group1: def foo(
    # group2: params
    # group3: ):
    # Meanwhile ignoring `self` which is added by cheetah
    r'^\s+(def [A-Za-z0-9_]+\()self(?:, )?(.*?)(\):)$'
)
STRIP_SYMBOLS_RE = re.compile(r'[^A-Za-z0-9_]')
NEED_LINE_NUMBER_NORMALIZED = frozenset({'F402', 'F811', 'F812'})
IMPORT_TYPE_CODES = frozenset({'F401', 'F403', 'F811'})


class LineNoHint(object):
    FIRST_IMPORT = 'FIRST_IMPORT'
    LAST_IMPORT = 'LAST_IMPORT'


def _get_line_no_from_comments(py_line):
    """Return the line number parsed from the comment or 0."""
    matched = LINECOL_COMMENT_RE.match(py_line)
    if matched:
        return int(matched.group(1))
    else:
        return 0


def _find_bounds(py_line_no, py_by_line_no, cheetah_by_line_no):
    """Searches before and after in the python source to find comments which
    denote cheetah line numbers.  If a lower bound is not found, 0 is
    substituted.  If an upper bound is not found, len(cheetah lines) is
    returned.  The result is a lower-inclusive upper-exclusive range:
    [..., ...)
    """
    # Find lower bound
    for line_no in range(py_line_no, 0, -1):
        lower_bound = _get_line_no_from_comments(py_by_line_no[line_no])
        if lower_bound != 0:
            break
    else:
        lower_bound = 0

    # Find upper bound
    for line_no in range(py_line_no, len(py_by_line_no)):
        upper_bound = _get_line_no_from_comments(py_by_line_no[line_no])
        if upper_bound != 0:
            # Since we'll eventually be building a range(), let's make this
            # the non-inclusive upper-bound
            upper_bound += 1
            break
    else:
        upper_bound = len(cheetah_by_line_no)

    return lower_bound, upper_bound


def _fuzz_line(s):
    return STRIP_SYMBOLS_RE.sub('', s)


def _fuzz_py_line(s):
    # Normalize function definition lines to look more like the cheetah
    # equivalent
    return _fuzz_line(PY_DEF_RE.sub(r'\1\2\3', s))


def _fuzz_cheetah_line(s):
    # Normalize function definiton to look more like the python equivalent
    return _fuzz_line(s.replace('#block ', '#def '))


def _find_fuzzy_line(
        py_line_no, py_by_line_no, cheetah_by_line_no, prefer_first
):
    """Attempt to fuzzily find matching lines."""
    stripped_line = _fuzz_py_line(py_by_line_no[py_line_no])
    cheetah_lower_bound, cheetah_upper_bound = _find_bounds(
        py_line_no, py_by_line_no, cheetah_by_line_no,
    )

    sliced = list(enumerate(cheetah_by_line_no))[
        cheetah_lower_bound:cheetah_upper_bound
    ]
    if not prefer_first:
        sliced = reversed(sliced)

    for line_no, line in sliced:
        if stripped_line in _fuzz_cheetah_line(line):
            return line_no
    else:
        # We've failed to find a matching line
        return 0


def _get_line_no(py_line_no, py_by_line_no, cheetah_by_line_no, hint=None):
    # Attempt to find it by the cheetah compiler comments
    ret = _get_line_no_from_comments(py_by_line_no[py_line_no])
    if ret != 0:
        return ret

    # Try exact lines (usually imports)
    ret = _find_fuzzy_line(
        py_line_no,
        py_by_line_no,
        cheetah_by_line_no,
        prefer_first=hint is LineNoHint.FIRST_IMPORT,
    )
    if ret != 0:
        return ret

    # We've failed to intelligently determine the line number
    return 0


def _normalize_msg_line_no(msg, code, py_by_line_no, cheetah_by_line_no):
    if code not in NEED_LINE_NUMBER_NORMALIZED:
        return msg

    line_no = int(LINE_ERROR_MSG_RE.match(msg).group(2))
    new_line = five.text(_get_line_no(
        line_no, py_by_line_no, cheetah_by_line_no, LineNoHint.FIRST_IMPORT,
    ))
    return LINE_ERROR_MSG_RE.sub(r'\g<1>{}'.format(new_line), msg)


def _normalize_line(line_no, code, msg, py_by_line_no, cheetah_by_line_no):
    msg = _normalize_msg_line_no(msg, code, py_by_line_no, cheetah_by_line_no)
    line_no = _get_line_no(
        line_no, py_by_line_no, cheetah_by_line_no, LineNoHint.LAST_IMPORT,
    )
    return line_no, code, msg


def normalize_lines(data, py_lines, cheetah_lines):
    # Let's not think about the difference between index and line number
    py_by_line_no = ('',) + tuple(py_lines)
    cheetah_by_line_no = ('',) + tuple(cheetah_lines)
    return tuple(
        _normalize_line(line_no, code, msg, py_by_line_no, cheetah_by_line_no)
        for line_no, code, msg in data
    )


def check_flake8(py_lines):
    with tempfile.NamedTemporaryFile(suffix='.py') as tmpfile:
        tmpfile.write(''.join(py_lines).encode('UTF-8'))
        tmpfile.flush()
        cmd = (
            sys.executable, '-mflake8', tmpfile.name,
            '--format=%(row)s\t%(code)s\t%(text)s',
            '--select={}'.format(SELECTED_ERRORS),
        )
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        out, _ = proc.communicate()

    split = (line.split('\t') for line in out.decode().splitlines())
    ret = [(int(col), code, msg) for col, code, msg in split]
    return filter_known_errors(ret)


def to_readline(py_lines):
    it = iter(py_lines)

    def readline():
        try:
            return next(it)
        except StopIteration:
            return ''

    return readline


def check_unicode_literals(py_lines):
    data = ()
    readline = to_readline(py_lines)

    for token_type, token_s, start, _, _ in tokenize.generate_tokens(readline):
        if token_type == tokenize.STRING and token_s.startswith(('u', 'U')):
            data += ((
                start[0],
                'P001',
                'unicode literal prefix is unnecessary (assumed) in '
                'cheetah templates: {}'.format(token_s),
            ),)
    return data


PY_CHECKS = (
    check_flake8,
    check_unicode_literals,
)


def get_from_py(file_contents):
    data = ()
    cheetah_lines = file_contents.splitlines(True)
    py_source = to_py(file_contents)
    py_lines = py_source.splitlines(True)
    for check in PY_CHECKS:
        data += normalize_lines(check(py_lines), py_lines, cheetah_lines)
    return data


def check_implements(cheetah_by_line_no):
    extends = None
    implements = None
    for line_no, line in enumerate(cheetah_by_line_no):
        if line.startswith('#extends'):
            extends = (line_no, line)
        elif line.startswith('#implements'):
            implements = (line_no, line)

    if (
            not extends and
            implements and
            implements[1].strip() == '#implements respond'
    ):
        return (
            (
                implements[0],
                'T001', "'#implements respond' is assumed without '#extends'"
            ),
        )
    else:
        return ()


def check_extends_cheetah_template(cheetah_by_line_no):
    for line_no, line in enumerate(cheetah_by_line_no):
        if line.strip() == '#extends Cheetah.Template':
            return (
                (
                    line_no,
                    'T002',
                    "'#extends Cheetah.Template' "
                    "is assumed without '#extends'",
                ),
            )
    return ()


LEADING_WHITESPACE = re.compile('^[ \t]+')


def check_indentation(cheetah_by_line_no):
    errors = []
    for line_no, line in enumerate(cheetah_by_line_no):
        ws = getattr(LEADING_WHITESPACE.match(line), 'group', lambda: '')()
        if '\t' in ws:
            errors.append((line_no, 'T003', 'Indentation contains tabs'))
        elif len(ws) % 4 != 0:
            errors.append((
                line_no, 'T004', 'Indentation is not a multiple of 4',
            ))
    return tuple(errors)


def check_empty(cheetah_by_line_no):
    if not ''.join(cheetah_by_line_no).strip():
        return ((1, 'T005', 'File is empty'),)
    else:
        return ()


LINE_CHECKS = (
    check_implements,
    check_extends_cheetah_template,
    check_indentation,
    check_empty,
)


def get_from_lines(file_contents):
    cheetah_by_line_no = ('',) + tuple(file_contents.splitlines(True))
    data = ()
    for check in LINE_CHECKS:
        data += check(cheetah_by_line_no)
    return data


def get_flakes(file_contents):
    data = ()
    data += get_from_py(file_contents)
    data += get_from_lines(file_contents)
    return tuple(sorted(data))


def flake(filename):
    file_contents = read_file(filename)
    flakes = get_flakes(file_contents)
    for lineno, code, msg in flakes:
        print(five.n('{}:{} {} {}'.format(filename, lineno, code, msg)))
    return int(bool(flakes))


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*', help='Filenames to flake.')
    args = parser.parse_args(argv)

    retv = 0
    for filename in args.filenames:
        retv |= flake(filename)
    return retv


if __name__ == '__main__':
    exit(main())
