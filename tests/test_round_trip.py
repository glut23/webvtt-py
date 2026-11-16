import pathlib
import tempfile
import unittest

import webvtt
from webvtt.models import Caption, Style

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


class TestPlainTextConversions(unittest.TestCase):

    def test_srt_sbv_literal_text_is_encoded_as_cue_text(self):
        for format, header in (
                ('srt', '1\n00:00:01,000 --> 00:00:02,000\n'),
                ('sbv', '0:00:01.000,0:00:02.000\n')):
            for text, cue_text in (
                    ('&amp;', '&amp;amp;'),
                    ('&amp;lt;', '&amp;amp;lt;'),
                    ('&copy;', '&amp;copy;'), ('\xa0', '\xa0'),
                    ('<3 you >', '&lt;3 you &gt;'),
                    ('<foo>x</foo>', '&lt;foo&gt;x&lt;/foo&gt;'),
                    ('if a < b\nthen b > a',
                     'if a &lt; b\nthen b &gt; a'),
                    ('a --> b', 'a --&gt; b')):
                with self.subTest(format=format, text=text):
                    vtt = webvtt.from_string(header + text + '\n',
                                              format=format)
                    self.assertEqual(len(vtt), 1)
                    self.assertEqual(vtt[0].text, text)
                    self.assertEqual(vtt[0].raw_text, cue_text)
                    self.assertEqual(webvtt.from_string(vtt.content), vtt)

    def test_srt_sbv_exports_preserve_resolved_text(self):
        for format, keep_formatting in (('srt', False), ('srt', True),
                                         ('sbv', False)):
            for cue_text, expected in (('&amp;lt;', '&lt;'),
                                       ('&am<b></b>p;', '&amp;'),
                                       ('1\na --&gt; b', '1\na --> b'),
                                       ('2 &lt; 3\n1\na --&gt; b',
                                        '2 < 3\n1\na --> b')):
                with self.subTest(format=format,
                                  keep_formatting=keep_formatting,
                                  cue_text=cue_text):
                    vtt = webvtt.WebVTT(captions=[Caption(
                        '00:00:01.000', '00:00:02.000', cue_text)])
                    output = vtt.to_string(format, keep_formatting)
                    restored = webvtt.from_string(output, format=format)
                    self.assertEqual([c.text for c in restored], [expected])

    def test_srt_sbv_exports_preserve_nonbreaking_space_lines(self):
        for format, keep_formatting in (('srt', False), ('srt', True),
                                         ('sbv', False)):
            for cue_text, expected in (
                    ('&nbsp;', '\xa0'),
                    ('first\n&nbsp;\n \nlast', 'first\n\xa0\nlast')):
                with self.subTest(format=format,
                                  keep_formatting=keep_formatting,
                                  cue_text=cue_text):
                    vtt = webvtt.WebVTT(captions=[Caption(
                        '00:00:01.000', '00:00:02.000', cue_text)])
                    output = vtt.to_string(format, keep_formatting)
                    self.assertIn('\xa0', output)
                    restored = webvtt.from_string(output, format=format)
                    self.assertEqual([c.text for c in restored], [expected])

    def test_srt_formatting_decodes_text_tokens_once(self):
        cue_text = ('<b>&amp;lt;</b> <i>&copy;</i> <u>under</u> '
                    '<font color=red>&amp;amp;</font>')
        vtt = webvtt.WebVTT(captions=[Caption(
            '00:00:01.000', '00:00:02.000', cue_text)])
        output = vtt.to_string('srt', keep_formatting=True)
        self.assertIn('<b>&lt;</b> <i>\xa9</i> <u>under</u> '
                      '<font color=red>&amp;</font>', output)
        restored = webvtt.from_string(output, format='srt')
        self.assertEqual(restored[0].text, '&lt; \xa9 under &amp;')
        self.assertIn('<b>&amp;lt;</b>', restored[0].raw_text)
        self.assertIn('<i>\xa9</i> <u>under</u>', restored[0].raw_text)
        self.assertEqual(restored.styles[0].lines[1], '  color: red;')
        vtt = webvtt.WebVTT(captions=[Caption(
            '00:00:01.000', '00:00:02.000', '<b>2 &lt; 3</b>')])
        output = vtt.to_string('srt', keep_formatting=True)
        self.assertIn('<b>2 < 3</b>', output)
        restored = webvtt.from_string(output, format='srt')
        self.assertEqual(restored[0].text, '2 < 3')
        self.assertEqual(restored[0].raw_text, '<b>2 &lt; 3</b>')

    def test_webvtt_preserves_text_and_formatting_not_representable_in_srt(self):
        for cue_text, plain_text in (
                ('&lt;b&gt;literal&lt;/b&gt;', '<b>literal</b>'),
                ('&lt;i&gt;x&lt;/i&gt;', '<i>x</i>'),
                ('&lt;u&gt;x&lt;/u&gt;', '<u>x</u>'),
                ('&lt;font color=red&gt;x&lt;/font&gt;',
                 '<font color=red>x</font>'),
                (r'{\an8}literal', r'{\an8}literal'),
                ('&lt;<c></c>b&gt;x', '<b>x'),
                ('&lt;<b>x</b>', '<x')):
            with self.subTest(cue_text=cue_text), \
                    tempfile.TemporaryDirectory() as folder:
                original_srt = pathlib.Path(folder) / 'original.srt'
                original_srt.write_bytes(b'original subtitle file\r\n')
                output = pathlib.Path(folder) / 'preserved.vtt'
                caption = Caption(
                    '00:00:01.000', '00:00:02.000',
                    '<v Bob>' + cue_text + '\n<i>formatted</i></v>',
                    identifier='cue-1', settings='align:start')
                vtt = webvtt.WebVTT(captions=[caption],
                                    styles=[Style('::cue { color: red; }')])
                self.assertEqual(caption.text, plain_text + '\nformatted')
                self.assertEqual(caption.voice, 'Bob')
                content = vtt.to_string('vtt')
                self.assertTrue(content.startswith('WEBVTT\n'))
                self.assertEqual(webvtt.from_string(content), vtt)
                vtt.save(output)
                self.assertTrue(output.read_text(encoding='utf-8')
                                .startswith('WEBVTT\n'))
                restored = webvtt.read(output)
                self.assertEqual(restored, vtt)
                self.assertEqual(restored[0].lines, caption.lines)
                self.assertEqual(restored[0].raw_text, caption.raw_text)
                self.assertEqual(restored[0].text, caption.text)
                self.assertEqual(restored[0].voice, 'Bob')
                self.assertEqual(restored.styles, vtt.styles)
                self.assertEqual(restored[0].settings, caption.settings)
                self.assertEqual(original_srt.read_bytes(),
                                 b'original subtitle file\r\n')

    def test_sbv_preserves_literal_tags_without_markup(self):
        vtt = webvtt.WebVTT(captions=[Caption(
            '00:00:01.000', '00:00:02.000',
            '&lt;b&gt;literal&lt;/b&gt;')])
        output = vtt.to_string('sbv')
        self.assertIn('<b>literal</b>', output)
        restored = webvtt.from_string(output, format='sbv')
        self.assertEqual(restored[0].text, '<b>literal</b>')
        self.assertEqual(restored, vtt)
