import os
import pathlib
import unittest
import tempfile
from unittest import mock

from webvtt.utils import (
    FileWrapper,
    CODEC_BOMS,
    iter_blocks_of_lines,
    _split_lines,
    _write_text_file
    )

from .helpers import named_temporary_file


class TestUtils(unittest.TestCase):

    def test_open_file(self):
        with named_temporary_file('w') as f:
            f.write('Hello test!')
            f.flush()
            with FileWrapper.open(f.name) as fw:
                self.assertEqual(fw.file.read(), 'Hello test!')
                self.assertEqual(fw.file.encoding, 'utf-8')

    def test_open_file_with_bom(self):
        for encoding, bom in CODEC_BOMS.items():
            with named_temporary_file('wb') as f:
                f.write(bom)
                f.write('Hello test'.encode(encoding))
                f.flush()

                with FileWrapper.open(f.name) as fw:
                    self.assertEqual(fw.file.read(), 'Hello test')
                    self.assertEqual(fw.file.encoding, encoding)

    def test_write_text_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / 'captions.vtt'
            path.write_text('old')

            _write_text_file(str(path), 'WEBVTT\n\nCafé\n', 'utf-8')

            self.assertEqual(
                path.read_bytes(),
                f'WEBVTT{os.linesep}{os.linesep}Café{os.linesep}'.encode()
                )

    def test_write_text_file_default_encoding(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = pathlib.Path(temp_dir) / 'captions.vtt'

            with mock.patch('locale.getpreferredencoding',
                            return_value='utf-16-le'):
                _write_text_file(str(path), 'Café')

            self.assertEqual(path.read_bytes(), 'Café'.encode('utf-16-le'))

    def test_write_text_file_encoding_error_keeps_file(self):
        for encoding, error in (('ascii', UnicodeEncodeError),
                                ('no-such-encoding', LookupError),
                                ('', LookupError)):
            with self.subTest(encoding=encoding):
                with tempfile.TemporaryDirectory() as temp_dir:
                    path = pathlib.Path(temp_dir) / 'captions.vtt'
                    path.write_text('old')

                    with self.assertRaises(error):
                        _write_text_file(str(path), 'Café', encoding)

                    self.assertEqual(path.read_text(), 'old')

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
                self.assertListEqual(_split_lines(text), text.splitlines())

    def test_split_lines_only_on_cr_and_lf(self):
        self.assertListEqual(
            _split_lines('a\x0bb\x0cc\x1cd\x1de\x1ef\x85g\u2028h\u2029i\nj'),
            ['a\x0bb\x0cc\x1cd\x1de\x1ef\x85g\u2028h\u2029i', 'j']
            )
