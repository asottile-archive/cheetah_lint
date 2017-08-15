# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import io
import sys

import lxml.etree
from aspy.refactor_imports.sort import sort
from refactorlib.cheetah.parse import parse
from refactorlib.node import ExactlyOneError

from cheetah_lint.directives import get_all_imports
from cheetah_lint.directives import get_compiler_settings_directive
from cheetah_lint.directives import get_extends_directive
from cheetah_lint.directives import get_implements_directive
from cheetah_lint.imports import combine_import_objs
from cheetah_lint.util import read_file


def separate_comma_imports(xmldoc):
    imports = get_all_imports(xmldoc)

    for import_obj in imports:
        if import_obj.import_obj.has_multiple_imports:
            import_obj.directive_element.replace_self(
                import_obj.get_new_import_statements()
            )

    return xmldoc.totext(encoding='unicode')


def remove_duplicated_imports(xmldoc):
    previously_seen_imports = set()
    for import_obj in get_all_imports(xmldoc):
        if import_obj.import_obj in previously_seen_imports:
            import_obj.directive_element.remove_self()
        else:
            previously_seen_imports.add(import_obj.import_obj)
    return xmldoc.totext(encoding='unicode')


def apply_import_ordering(xmldoc):
    compiler_settings = get_compiler_settings_directive(xmldoc)
    extends = get_extends_directive(xmldoc)
    implements = get_implements_directive(xmldoc)
    initial_block = [
        obj for obj in [compiler_settings, extends, implements]
        if obj is not None
    ]

    cheetah_imports = get_all_imports(xmldoc)
    # Remove all of the elements from the document
    for cheetah_import in cheetah_imports:
        cheetah_import.directive_element.remove_self()

    sorted_blocks = sort([
        cheetah_import.import_obj for cheetah_import in cheetah_imports
    ])

    element = lxml.etree.Element('Imports')
    element.text = '\n'.join(
        combine_import_objs(block) for block in sorted_blocks
    )
    xmldoc.insert(0, element)

    if initial_block:
        ws_element = lxml.etree.Element('Whitespace')
        ws_element.text = '\n'
        xmldoc.insert(0, ws_element)
        for directive in reversed(initial_block):
            directive.remove_self()
            xmldoc.insert(0, directive)

    return xmldoc.totext(encoding='unicode')


def fix_whitespace_after_imports(xmldoc):
    try:
        last_directive = xmldoc.xpath_one(
            """(
                //cheetah/*[
                    self::compiler-settings or
                    self::Directive and (
                        starts-with(., "#extends") or
                        starts-with(., "#implements") or
                        SimpleExprDirective/UnbracedExpression/Py[1][
                            text() = 'from' or text() = 'import'
                        ]
                    )
                ]
            )[last()]
            """
        )
        following_whitespace_element = last_directive.xpath_one(
            'following-sibling::*[1]',
        )
    except ExactlyOneError:
        # The document either contains no directives or has no body
        return xmldoc.totext(encoding='unicode')

    following_whitespace_element.text = (
        '\n\n' + following_whitespace_element.text.lstrip('\n')
    )
    return xmldoc.totext(encoding='unicode').rstrip('\n') + '\n'


def perform_step(file_contents, step):
    """Performs a step of the transformation.

    :param text file_contents: Contends of the cheetah template
    :param function step: Function taking xmldoc and returning new contents
    :returns: new contents of the file.
    """
    assert type(file_contents) is not bytes
    xmldoc = parse(file_contents)
    return step(xmldoc)


STEPS = [
    separate_comma_imports,
    remove_duplicated_imports,
    apply_import_ordering,
    fix_whitespace_after_imports,
]


def main(argv=None):
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*')
    args = parser.parse_args(argv)

    retv = 0
    for filename in args.filenames:
        original_contents = file_contents = read_file(filename)

        for step in STEPS:
            file_contents = perform_step(file_contents, step)

        if file_contents != original_contents:
            retv = 1
            print('Reordered imports in {}'.format(filename))
            with io.open(filename, 'w') as file_obj:
                file_obj.write(file_contents)

    return retv


if __name__ == '__main__':
    exit(main())
