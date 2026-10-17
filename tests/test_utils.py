import unittest
import tempfile

from webvtt.utils import FileWrapper, CODEC_BOMS, iter_blocks_of_lines


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
