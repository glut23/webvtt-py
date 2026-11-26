import os
import pathlib
import stat
import unittest
import tempfile
from unittest import mock

from webvtt.utils import (
    FileWrapper,
    CODEC_BOMS,
    iter_blocks_of_lines,
    _iter_numbered_blocks,
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

    def test_interrupted_write_keeps_previous_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / 'captions.vtt'
            path.write_bytes(b'previous captions')
            write_bytes = pathlib.Path.write_bytes

            def partial_write(destination, data):
                write_bytes(destination, data[:3])
                raise OSError('out of space')

            with mock.patch.object(pathlib.Path, 'write_bytes', partial_write):
                with self.assertRaisesRegex(OSError, 'out of space'):
                    _write_text_file(path, 'new captions')
            self.assertEqual(path.read_bytes(), b'previous captions')
            self.assertEqual(list(path.parent.iterdir()), [path])

    def test_write_through_symbolic_link(self):
        with tempfile.TemporaryDirectory() as folder:
            root = pathlib.Path(folder)
            target = root / 'target.vtt'
            link = root / 'link.vtt'
            try:
                link.symlink_to(target.name)
            except OSError as exc:
                self.skipTest(f'cannot create symbolic link: {exc}')
            for text in ('first', 'second'):
                _write_text_file(link, text)
                self.assertTrue(link.is_symlink())
                self.assertEqual(target.read_text(), text)

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX file modes')
    def test_write_permissions(self):
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / 'captions.vtt'
            ordinary = pathlib.Path(folder) / 'ordinary'
            ordinary.write_bytes(b'')
            _write_text_file(path, 'first')
            self.assertEqual(stat.S_IMODE(path.stat().st_mode),
                             stat.S_IMODE(ordinary.stat().st_mode))
            path.chmod(0o640)
            _write_text_file(path, 'second')
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o640)

    def test_write_to_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(OSError):
                _write_text_file(folder, 'captions')
            self.assertTrue(pathlib.Path(folder).is_dir())

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'requires a FIFO')
    def test_write_to_fifo(self):
        with tempfile.TemporaryDirectory() as folder:
            fifo = pathlib.Path(folder) / 'captions.vtt'
            os.mkfifo(fifo)
            reader = os.open(fifo, os.O_RDONLY | os.O_NONBLOCK)
            try:
                _write_text_file(fifo, 'captions', 'utf-8')
                self.assertTrue(stat.S_ISFIFO(fifo.stat().st_mode))
                self.assertEqual(os.read(reader, 8), b'captions')
            finally:
                os.close(reader)

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

    def test_iter_numbered_blocks(self):
        for lines, blocks in (
                ([], []),
                (['', ' '], []),
                (['block'], [(1, ['block'])]),
                (['block', ''], [(1, ['block'])]),
                (['', '', 'a', 'b', ' ', '', 'c', 'd'],
                 [(3, ['a', 'b']), (7, ['c', 'd'])]),
                ):
            with self.subTest(lines=lines):
                self.assertListEqual(
                    list(_iter_numbered_blocks(lines)),
                    blocks
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
