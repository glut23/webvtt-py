import pathlib
import tempfile
import unittest

import webvtt

PATH_TO_SAMPLES = pathlib.Path(__file__).resolve().parent / 'samples'

# the samples that are not read, as they are not valid for their format
INVALID_SAMPLES = {
    'empty.vtt', 'invalid.vtt', 'invalid_format.sbv', 'invalid_format1.srt',
    'invalid_format2.srt', 'invalid_format3.srt', 'invalid_format4.srt',
    }


def _samples():
    """Return the samples that are read, with their format."""
    return [
        (path, path.suffix[1:])
        for path in sorted(PATH_TO_SAMPLES.iterdir())
        if path.name not in INVALID_SAMPLES
        ]


def _read(path, format):
    if format == 'vtt':
        return webvtt.read(path)
    return getattr(webvtt, f'from_{format}')(path)


class TestRoundTrip(unittest.TestCase):

    def test_invalid_samples_exist(self):
        for name in INVALID_SAMPLES:
            with self.subTest(name=name):
                self.assertTrue((PATH_TO_SAMPLES / name).is_file())

    def test_samples_to_vtt_and_back(self):
        for path, format in _samples():
            with self.subTest(sample=path.name):
                vtt = _read(path, format)
                self.assertEqual(webvtt.from_string(vtt.content), vtt)

    def test_samples_saved_and_read_again(self):
        for path, format in _samples():
            with self.subTest(sample=path.name), \
                    tempfile.TemporaryDirectory() as folder:
                vtt = _read(path, format)
                output = pathlib.Path(folder) / path.name
                if format == 'vtt':
                    vtt.save(output)
                elif format == 'srt':
                    # the formatting is read back from SRT as it was
                    vtt.save_as_srt(output, keep_formatting=True)
                else:
                    vtt.save_as_sbv(output)
                saved = _read(output, format)
                self.assertEqual(saved, vtt)
                self.assertEqual(saved.encoding, vtt.encoding)
