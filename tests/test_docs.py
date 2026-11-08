"""
Run the code examples of the documentation against the fixtures.

The Python code blocks of a document run in order, sharing their names, as
some continue an earlier one. Each runs in a new folder with the files of
``doc_fixtures``, so the files the earlier blocks saved are not there.

An expression whose comment is a Python literal, at the end of its line or
on the lines right after it, must give that value, and a string ending with
``...`` only the text before it. A ``print`` call followed by comment lines
must print them.
"""

import ast
import contextlib
import io
import os
import pathlib
import re
import shutil
import sys
import tempfile
import textwrap
import tokenize
import types
import unittest
import unittest.mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = pathlib.Path(__file__).resolve().parent / 'doc_fixtures'

# folders the examples save to, which must exist
FOLDERS = ('other/folder',)

_TITLE = re.compile(r'^(\S.*)\n[=-]{3,}$', re.MULTILINE)
# the indented lines after the directive, and the empty lines among them
_CODE_BLOCK = re.compile(r'^\.\. code-block:: python\n((?:\n| .*\n)+)',
                         re.MULTILINE)


def _examples(path):
    """
    Return the Python code blocks of a reStructuredText document.

    :returns: tuples of the section title, the line number of the
        ``code-block`` directive and the code, which starts on the next line
    """
    text = path.read_text(encoding='utf-8') + '\n'
    titles = [(match.start(), match.group(1))
              for match in _TITLE.finditer(text)]
    examples = []
    for match in _CODE_BLOCK.finditer(text):
        section = next(
            (title for start, title in reversed(titles)
             if start < match.start()),
            None
            )
        lineno = text.count('\n', 0, match.start()) + 1
        examples.append((section, lineno, textwrap.dedent(match.group(1))))
    return examples


def _comments(code):
    """Return the comments of the code by line, and the lines with code."""
    comments = {}
    code_lines = set()
    for token in tokenize.generate_tokens(io.StringIO(code).readline):
        if token.type == tokenize.COMMENT:
            comments[token.start[0]] = token.string[1:]
        elif token.type not in (tokenize.NL, tokenize.NEWLINE,
                                tokenize.INDENT, tokenize.DEDENT,
                                tokenize.ENDMARKER):
            code_lines.update(range(token.start[0], token.end[0] + 1))
    return comments, code_lines


def _is_print(node):
    return (isinstance(node, ast.Call) and
            isinstance(node.func, ast.Name) and node.func.id == 'print' and
            len(node.args) == 1 and not node.keywords)


class _Checks(ast.NodeTransformer):
    """
    Turn the expressions with an expected value into checks.

    The checks are given the line of the document they are on, which are
    kept in ``lines``.
    """

    def __init__(self, code, offset):
        self.comments, self.code_lines = _comments(code)
        self.offset = offset
        self.lines = set()

    def _following_comments(self, node):
        lines = []
        lineno = node.end_lineno + 1
        while lineno in self.comments and lineno not in self.code_lines:
            text = self.comments[lineno]
            lines.append(text[1:] if text.startswith(' ') else text)
            lineno += 1
        return lines

    def visit_Expr(self, node):
        if _is_print(node.value):
            lines = self._following_comments(node)
            if not lines:
                return node
            check, value = '__check_output__', node.value.args[0]
            expected = '\n'.join(lines)
        else:
            comment = self.comments.get(node.end_lineno)
            if comment is None:
                comment = ' '.join(self._following_comments(node))
            try:
                ast.literal_eval(comment.strip())
            except (SyntaxError, ValueError):
                return node
            check, value, expected = '__check__', node.value, comment.strip()
        lineno = node.lineno + self.offset
        self.lines.add(lineno)
        call = ast.Call(
            func=ast.Name(check, ast.Load()),
            args=[value, ast.Constant(expected), ast.Constant(lineno)],
            keywords=[]
            )
        return ast.copy_location(ast.Expr(call), node)


@contextlib.contextmanager
def _fixtures():
    """Run in a new folder with the fixtures."""
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as folder:
        for fixture in FIXTURES.iterdir():
            shutil.copy(fixture, folder)
        for name in FOLDERS:
            os.makedirs(os.path.join(folder, name))
        os.chdir(folder)
        try:
            yield
        finally:
            os.chdir(cwd)


def _requests():
    """Return a requests module whose get gives the captions fixture."""
    response = types.SimpleNamespace(
        text=(FIXTURES / 'captions.vtt').read_text(encoding='utf-8')
        )
    module = types.ModuleType('requests')
    module.get = lambda url: response
    return module


class TestDocs(unittest.TestCase):

    def run_examples(self, path):
        """Run the examples of a document and return the lines checked."""
        if not path.exists():
            self.skipTest(f'{path.name} is not available')
        examples = _examples(path)
        # every block is found, also one the pattern would not match
        self.assertEqual(
            len(examples),
            path.read_text(encoding='utf-8').count('code-block:: python')
            )
        checked = set()

        def compare(value, expected, lineno):
            checked.add(lineno)
            if (isinstance(value, str) and isinstance(expected, str) and
                    expected.endswith('...')):
                value = value[:len(expected) - 3] + '...'
            # a failure shows the line of the document in its traceback
            self.assertEqual(value, expected)

        def check(value, literal, lineno):
            compare(value, ast.literal_eval(literal), lineno)

        def check_output(value, expected, lineno):
            compare(str(value).rstrip('\n'), expected, lineno)

        namespace = {
            '__name__': '__docs__',
            '__check__': check,
            '__check_output__': check_output,
            }
        checks = set()
        with unittest.mock.patch.dict(sys.modules, requests=_requests()):
            for section, lineno, code in examples:
                with self.subTest(section=section, line=lineno), \
                        _fixtures(), \
                        contextlib.redirect_stdout(io.StringIO()):
                    transformer = _Checks(code, lineno)
                    tree = transformer.visit(ast.parse(code))
                    checks.update(transformer.lines)
                    ast.fix_missing_locations(tree)
                    ast.increment_lineno(tree, lineno)
                    exec(compile(tree, str(path), 'exec'), namespace)
        # a check in a loop or a branch that did not run checks nothing
        self.assertEqual(sorted(checks - checked), [],
                         'lines of checks that did not run')
        return checks

    def test_usage(self):
        checks = self.run_examples(ROOT / 'docs' / 'source' / 'usage.rst')
        self.assertTrue(checks)

    def test_readme(self):
        self.run_examples(ROOT / 'README.rst')
