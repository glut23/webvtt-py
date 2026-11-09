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

    def test_srt_text_uses_webvtt_syntax(self):
        vtt = webvtt.from_string(
            '1\n00:00:00,000 --> 00:00:01,000\n'
            'Tom &amp; Jerry and I <3 you > all\n'
            'AT&T &notaref; &#60; and <b>bold</b>\n',
            format='srt'
            )
        caption = vtt[0]
        expected = webvtt.Caption(
            0, 1, 'Tom &amp; Jerry and I &lt;3 you > all\n'
            'AT&amp;T &amp;notaref; &lt; and <b>bold</b>'
            )
        self.assertEqual(caption, expected)
        self.assertEqual(repr(caption), repr(expected))
        self.assertEqual(caption.text, expected.text)
        self.assertEqual(caption.text,
                         'Tom & Jerry and I <3 you > all\n'
                         'AT&T &notaref; < and bold')
        self.assertEqual(webvtt.from_string(vtt.content), vtt)

        caption.text = 'Tom &amp; Jerry'
        self.assertEqual(caption.text, 'Tom & Jerry')
        self.assertEqual(webvtt.from_string(vtt.content), vtt)

    def test_srt_distinguishes_bold_from_literal_tags(self):
        source = (
            '1\n00:00:00,000 --> 00:00:01,000\na <b> c\n\n'
            '2\n00:00:01,000 --> 00:00:02,000\n'
            'a <b> c <B>bold <i>here</i>\n<u>and here</u></b>\n\n'
            '3\n00:00:02,000 --> 00:00:03,000\na </b> c\n'
            )
        vtt = webvtt.from_string(source, format='srt')
        self.assertEqual(
            [c.text for c in vtt], ['a <b> c', 'a <b> c bold here\nand here',
                                    'a </b> c']
            )
        self.assertEqual(
            vtt[1].raw_text,
            'a &lt;b> c <b>bold <i>here</i>\n<u>and here</u></b>'
            )
        self.assertEqual(webvtt.from_string(vtt.content), vtt)
        formatted = vtt.to_string('srt', keep_formatting=True)
        self.assertIn('a <b> c <b>bold <i>here</i>\n<u>and here</u></b>',
                      formatted)
        self.assertEqual(webvtt.from_string(formatted, format='srt'), vtt)

    def test_legacy_srt_references_survive_file_round_trip(self):
        legacy = (
            '1\n00:00:00,000 --> 00:00:01,000\n'
            'Tom &amp; Jerry, 2 &#60; 3, &copy; and 4 &#x3E; 1\n\n'
            '2\n00:00:01,000 --> 00:00:02,000\n&nbsp;\n'
            )
        for keep_formatting in (False, True):
            with self.subTest(keep_formatting=keep_formatting), \
                    tempfile.TemporaryDirectory() as folder:
                path = pathlib.Path(folder)
                (path / 'legacy.srt').write_text(legacy, encoding='utf-8')
                imported = webvtt.from_srt(path / 'legacy.srt')
                imported.save_as_srt(path / 'export.srt',
                                     keep_formatting=keep_formatting)
                saved = webvtt.from_srt(path / 'export.srt')
                self.assertEqual([c.text for c in saved],
                                 ['Tom & Jerry, 2 < 3, \u00a9 and 4 > 1',
                                  '\xa0'])
                self.assertEqual(saved, imported)

    def test_legacy_srt_references_do_not_break_webvtt_lines(self):
        source = '1\n00:00:00,000 --> 00:00:01,000\na --&gt; b&#13;c&#10;d\n'
        vtt = webvtt.from_string(source, format='srt')

        self.assertEqual(vtt[0].text, 'a --> b\rc\nd')
        self.assertEqual(webvtt.from_string(vtt.content), vtt)

    def test_sbv_text_uses_webvtt_syntax(self):
        text = 'Tom & Jerry <b> and &copy;'
        source = f'0:00:00.000,0:00:01.000\n{text}\n'
        vtt = webvtt.from_string(source, format='sbv')

        self.assertEqual(vtt[0].text, text)
        self.assertEqual(vtt[0].raw_text,
                         'Tom &amp; Jerry &lt;b> and &amp;copy;')
        self.assertEqual(webvtt.from_string(vtt.content), vtt)
        self.assertEqual(vtt.to_string('sbv'), source)

    def test_srt_exports_decoded_text_with_and_without_formatting(self):
        vtt = webvtt.from_string(
            'WEBVTT\n\n00:00.000 --> 00:01.000\n'
            'Tom &amp; Jerry &lt;3 &amp;lt;\n'
            '<b>Bold</b> &lt;b&gt; &am<lang en></lang>p;\n'
            )
        for keep_formatting, bold in ((False, 'Bold'), (True, '<b>Bold</b>')):
            with self.subTest(keep_formatting=keep_formatting):
                self.assertEqual(
                    vtt.to_string('srt', keep_formatting=keep_formatting),
                    '1\n00:00:00,000 --> 00:00:01,000\n'
                    f'Tom & Jerry <3 &lt;\n{bold} <b> &amp;\n'
                    )

    def test_non_breaking_space_is_cue_text(self):
        vtt = webvtt.from_string('WEBVTT\n\n00:00.000 --> 00:01.000\n&nbsp;\n')

        self.assertEqual(vtt.validate(), [])
        for format, keep_formatting in (
            ('srt', False), ('srt', True), ('sbv', False)
        ):
            with self.subTest(format=format, keep_formatting=keep_formatting):
                output = vtt.to_string(format, keep_formatting=keep_formatting)
                self.assertTrue(output.endswith('\n\xa0\n'))
                read_back = webvtt.from_string(output, format=format)
                self.assertEqual(len(read_back), 1)
                self.assertEqual(read_back[0].text, '\xa0')
                self.assertEqual(webvtt.from_string(read_back.content), read_back)

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
