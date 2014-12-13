from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import io
import re
import sys

import pep8
from Cheetah.compile import compile_source
from Cheetah.legacy_compiler import LegacyCompiler
from Cheetah.legacy_parser import LegacyParser
from flake8.engine import get_style_guide
from refactorlib.cheetah.parse import AutoDict

from cheetah_lint import five


ACCEPTABLE_UNUSED_ASSIGNMENTS = ('_dummyTrans', '_filter', 'write', 'SL')
UNUSED_ASSIGNMENTS_FLAKE8_MESSAGES = frozenset(
    "F841 local variable '{0}' is assigned to but never used".format(name)
    for name in ACCEPTABLE_UNUSED_ASSIGNMENTS
)


ACCEPTABLE_UNUSED_IMPORTS = ('NotFound', 'Template', 'VFN', 'VFFSL', 'VFSL')
UNUSED_IMPORTS_FLAKE8_MESSAGES = frozenset(
    "F401 '{0}' imported but unused".format(name)
    for name in ACCEPTABLE_UNUSED_IMPORTS
)


# The cheetah compiler produces problems with the following things given
# completely valid code:
# - Whitespace
# - undefined name 'name' - Variables referenced from the searchlist appear as
#   undefined variables when linting.
# Because of this, we select the errors we know to be actual problems
SELECTED_ERRORS = set((
    # 'module' imported but unused
    'F401',
    # import 'module' from line N shadowed by loop variable
    'F402',
    # 'from module import *' used; unable to detect undefined names
    'F403',
    # redefinition of unused 'name' from line N
    'F811',
    # list comprehension redefineds 'name' from line N
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
    'E901',
    # .has_key() is deprecated, use 'in'
    'W601',
))


class AllMacrosTrivialParser(LegacyParser):  # noqa  # pylint:disable=too-many-public-methods
    """An instrumented parser which interprets any macro trivially."""

    def __init__(self, *args, **kwargs):
        super(AllMacrosTrivialParser, self).__init__(*args, **kwargs)
        # Default unknown directives to macros
        self._directiveNamesAndParsers = AutoDict(
            lambda: self.eatMacroCall,
            self._directiveNamesAndParsers,
        )
        # Default all macros to trivial
        self._macros = AutoDict(lambda: lambda src: src)

    def eatCompilerSettings(self):
        # Don't want compiler-settings to affect output
        self.advance(len('compiler-settings'))
        self._eatToThisEndDirective('compiler-settings')


class AllMacrosTrivialCompiler(LegacyCompiler):
    parserClass = AllMacrosTrivialParser


def to_py(src):
    return compile_source(
        src,
        # This turns off the usual $var -> VFFSL(SL, 'var', True, True)
        # so now we get $var -> var
        settings={'useNameMapper': False},
        compiler_cls=AllMacrosTrivialCompiler,
    )


class DataCollectingReporter(pep8.BaseReport):
    """A Reporter for pep8/flake8 which simply collects data instead of
    spewing to stdout.
    """

    def __init__(self, *args, **kwargs):
        super(DataCollectingReporter, self).__init__(*args, **kwargs)
        self.data = []

    def error(self, line_number, offset, text, check):
        # XXX: Restore ignoring behaviour from baseclass (copied from pep8)
        if self._ignore_code(text[:4]):
            return
        self.data.append((line_number, text))


def filter_known_unused_assignments(data):
    return tuple(
        (line, msg)
        for line, msg in data
        if msg not in UNUSED_ASSIGNMENTS_FLAKE8_MESSAGES
    )


def filter_known_unused_imports(data):
    return tuple(
        (line, msg)
        for line, msg in data
        if msg not in UNUSED_IMPORTS_FLAKE8_MESSAGES
    )


LINECOL_COMMENT_RE = re.compile(r'^.+#.+line (\d+), col \d+')
LINE_ERROR_MSG_RE = re.compile(r'^(.+from line )(\d+)')
PY_DEF_RE = re.compile(
    # A bit complicated, but gets these interesting bits from a function def:
    # group1: def foo(
    # group2: params
    # group3: ):
    # Meanwhile ignoring `self`, `**KWS` which are added by cheetah
    r'^\s+(def [A-Za-z0-9_]+\()self, (.*?)(?:(?:, )?\*\*KWS)?(\):)$'
)
STRIP_SYMBOLS_RE = re.compile(r'[^A-Za-z0-9_]')
NEED_LINE_NUMBER_NORMALIZED = frozenset(('F402', 'F811', 'F812'))
IMPORT_TYPE_CODES = frozenset(('F401', 'F403', 'F811'))


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


def _normalize_msg_line_no(msg, py_by_line_no, cheetah_by_line_no):
    code = msg[:4]
    if code not in NEED_LINE_NUMBER_NORMALIZED:
        return msg

    line_no = int(LINE_ERROR_MSG_RE.match(msg).group(2))
    new_line = five.text(_get_line_no(
        line_no, py_by_line_no, cheetah_by_line_no, LineNoHint.FIRST_IMPORT,
    ))
    return LINE_ERROR_MSG_RE.sub(r'\g<1>{0}'.format(new_line), msg)


def _normalize_line_number(line_no, msg, py_by_line_no, cheetah_by_line_no):
    msg = _normalize_msg_line_no(msg, py_by_line_no, cheetah_by_line_no)
    line_no = _get_line_no(
        line_no, py_by_line_no, cheetah_by_line_no, LineNoHint.LAST_IMPORT,
    )
    return line_no, msg


def normalize_line_numbers(data, py_lines, cheetah_lines):
    # Let's not think about the difference between index and line number
    py_by_line_no = ('',) + tuple(py_lines)
    cheetah_by_line_no = ('',) + tuple(cheetah_lines)
    return tuple(
        _normalize_line_number(line_no, msg, py_by_line_no, cheetah_by_line_no)
        for line_no, msg in data
    )


def get_from_flake8(file_contents):
    cheetah_lines = file_contents.splitlines(True)
    py_source = to_py(file_contents)
    py_lines = py_source.splitlines(True)
    # Apologies, flake8 doesn't quite make this elegant / easy
    checker = get_style_guide(select=SELECTED_ERRORS)
    reporter = checker.init_report(DataCollectingReporter)
    checker.input_file('<compiled cheetah>', py_lines)
    data = filter_known_unused_assignments(filter_known_unused_imports(
        reporter.data,
    ))
    data = normalize_line_numbers(data, py_lines, cheetah_lines)
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
                "T001 '#implements respond' is assumed without '#extends'"
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
                    "T002 '#extends Cheetah.Template' "
                    "is assumed without '#extends'",
                ),
            )
    return ()


LINE_CHECKS = (check_implements, check_extends_cheetah_template)


def get_from_lines(file_contents):
    cheetah_by_line_no = ('',) + tuple(file_contents.splitlines(True))
    data = ()
    for check in LINE_CHECKS:
        data += check(cheetah_by_line_no)
    return data


def get_flakes(file_contents):
    data = ()
    data += get_from_flake8(file_contents)
    data += get_from_lines(file_contents)
    return tuple(sorted(data))


def flake(filename):
    file_contents = io.open(filename).read()
    flakes = get_flakes(file_contents)
    for lineno, msg in flakes:
        print('{0}:{1} {2}'.format(filename, lineno, msg))
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
