import unittest
import tempfile

from webvtt.utils import (
    FileWrapper,
    CODEC_BOMS,
    iter_blocks_of_lines,
    split_lines
    )


class TestUtils(unittest.TestCase):

    def test_open_file(self):
        with tempfile.NamedTemporaryFile('w') as f:
            f.write('Hello test!')
            f.flush()
            with FileWrapper.open(f.name) as fw:
                self.assertEqual(fw.file.read(), 'Hello test!')
                self.assertEqual(fw.file.encoding, 'utf-8')

    def test_open_file_with_bom(self):
        for encoding, bom in CODEC_BOMS.items():
            with tempfile.NamedTemporaryFile('wb') as f:
                f.write(bom)
                f.write('Hello test'.encode(encoding))
                f.flush()

                with FileWrapper.open(f.name) as fw:
                    self.assertEqual(fw.file.read(), 'Hello test')
                    self.assertEqual(fw.file.encoding, encoding)

    def test_iter_blocks_of_lines(self):
        self.assertListEqual(
            list(iter_blocks_of_lines(
                ['', 'block 1', 'line 2', ' ', '', 'block 2', '']
                )),
            [['block 1', 'line 2'], ['block 2']]
            )

    def test_split_lines(self):
        for text in ('',
                     '\n',
                     'line 1',
                     'line 1\n',
                     'line 1\r\nline 2\rline 3\nline 4',
                     'line 1\n\nline 2\r\n',
                     'line 1\r\r\n',
                     ):
            with self.subTest(text=text):
                self.assertListEqual(split_lines(text), text.splitlines())

    def test_split_lines_only_on_cr_and_lf(self):
        self.assertListEqual(
            split_lines('a\x0bb\x0cc\x1cd\x1de\x1ef\x85g\u2028h\u2029i\nj'),
            ['a\x0bb\x0cc\x1cd\x1de\x1ef\x85g\u2028h\u2029i', 'j']
            )
