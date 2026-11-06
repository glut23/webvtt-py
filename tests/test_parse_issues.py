import io
import pathlib
import tempfile
import unittest

import webvtt
from webvtt import sbv, srt
from webvtt.errors import (
    MalformedCaptionError,
    MalformedFileError,
    MalformedRegionError
    )
from webvtt import ParseIssue


class TestStrictErrorLocation(unittest.TestCase):

    def assert_error(self, content, error, line, message):
        with self.assertRaises(error) as cm:
            webvtt.from_string(content, strict=True)
        self.assertIs(type(cm.exception), error)
        self.assertTrue(
            str(cm.exception).startswith(f'line {line}: '),
            str(cm.exception)
            )
        self.assertIn(message, str(cm.exception))

    def test_cue_with_invalid_timestamp(self):
        self.assert_error(
            'WEBVTT\n\n00:00.000 --> 00:01.000\nok\n\n'
            '00:00.000 --> 00:99.000\nbad\n',
            MalformedCaptionError,
            6,
            '00:99.000'
            )

    def test_cue_timings_not_in_the_webvtt_format(self):
        self.assert_error(
            'WEBVTT\n\n\n\n0:0:3.540 --> 0:0:7.230\ntext\n',
            MalformedCaptionError,
            5,
            "Invalid cue block ['0:0:3.540 --> 0:0:7.230', 'text']"
            )

    def test_cue_with_identifier_is_located_at_the_identifier(self):
        self.assert_error(
            'WEBVTT\n\nid\n00:00:05.000 --> 00:00:01.000\ntext\n',
            MalformedCaptionError,
            3,
            'not after the start time'
            )

    def test_stray_block(self):
        self.assert_error(
            'WEBVTT\n\n00:00.000 --> 00:01.000\nok\n\nstray\n',
            MalformedCaptionError,
            6,
            "Invalid block ['stray']"
            )

    def test_style_after_a_cue(self):
        self.assert_error(
            'WEBVTT\n\n00:00.000 --> 00:01.000\nok\n\nSTYLE\na {}\n',
            MalformedCaptionError,
            6,
            'Style block after a cue'
            )

    def test_region_after_a_cue_keeps_the_error_type(self):
        self.assert_error(
            'WEBVTT\n\n00:00.000 --> 00:01.000\nok\n\nREGION\nid:a\n',
            MalformedRegionError,
            6,
            'Region block after a cue'
            )

    def test_region_setting_keeps_the_error_type(self):
        self.assert_error(
            'WEBVTT\n\nREGION\nunknown:a\n',
            MalformedRegionError,
            3,
            'region setting'
            )

    def test_header_with_arrow(self):
        self.assert_error(
            'WEBVTT a --> b\n\n00:00.000 --> 00:01.000\nok\n',
            MalformedCaptionError,
            1,
            'Invalid cue block'
            )

    def test_invalid_header(self):
        self.assert_error(
            'WEBVTTX\n\n00:00.000 --> 00:01.000\nok\n',
            MalformedFileError,
            1,
            "Invalid header 'WEBVTTX'"
            )

    def test_cue_without_empty_line_is_located_at_its_timings(self):
        self.assert_error(
            'WEBVTT\n\n00:00.000 --> 00:01.000\nok\n'
            '00:02.000 --> 00:03.000\nnext\n',
            MalformedCaptionError,
            5,
            'Invalid cue block'
            )

    def test_line_endings(self):
        for ending in ('\n', '\r\n', '\r'):
            with self.subTest(ending=ending):
                self.assert_error(
                    'WEBVTT\n\n00:00.000 --> 00:01.000\nok\n\nstray\n'.replace(
                        '\n', ending
                        ),
                    MalformedCaptionError,
                    6,
                    "Invalid block ['stray']"
                    )

    def test_read_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td, 'in.vtt')
            path.write_bytes(b'\xef\xbb\xbfWEBVTT\n\nstray\n')
            with self.assertRaises(MalformedCaptionError) as cm:
                webvtt.read(path, strict=True)
        self.assertEqual(str(cm.exception), "line 3: Invalid block ['stray']")


class TestVTTParseIssues(unittest.TestCase):

    def test_no_issues(self):
        vtt = webvtt.from_string(
            'WEBVTT\n\nNOTE comment\n\nSTYLE\na {}\n\n'
            'REGION\nid:a\n\n00:00.000 --> 00:01.000\nok\n'
            )
        self.assertEqual(vtt.parse_issues, [])

    def test_captions_not_read_have_no_issues(self):
        vtt = webvtt.WebVTT()
        self.assertEqual(vtt.parse_issues, [])
        vtt.parse_issues.append(ParseIssue(1, 'message', ['line']))
        self.assertEqual(webvtt.WebVTT().parse_issues, [])

    def test_skipped_cue(self):
        vtt = webvtt.from_string(
            'WEBVTT\n\n00:00.000 --> 00:01.000\nok\n\n'
            '00:00.000 --> 00:99.000\nbad\n'
            )
        self.assertEqual([c.text for c in vtt], ['ok'])
        self.assertEqual(len(vtt.parse_issues), 1)
        issue = vtt.parse_issues[0]
        self.assertEqual(issue.line, 6)
        self.assertEqual(issue.lines, ['00:00.000 --> 00:99.000', 'bad'])
        self.assertIn('00:99.000', issue.message)
        self.assertEqual(str(issue), f'line 6: {issue.message}')

    def test_message_is_the_error_of_strict_parsing(self):
        for name, content in (
                ('timings', 'WEBVTT\n\n00:00.-04 --> 00:04.300\nbad\n'),
                ('range', 'WEBVTT\n\n00:00:61.000 --> 00:00:62.000\nbad\n'),
                ('stray', 'WEBVTT\n\nstray\n'),
                ('notebook', 'WEBVTT\n\nNOTEBOOK\n'),
                ('arrow in note', 'WEBVTT\n\nNOTE a --> b\n'),
                ('style after cue',
                 'WEBVTT\n\n00:00.000 --> 00:01.000\nok\n\nSTYLE\na {}\n'),
                ('region after cue',
                 'WEBVTT\n\n00:00.000 --> 00:01.000\nok\n\nREGION\nid:a\n'),
                ('empty region', 'WEBVTT\n\nREGION\n')):
            with self.subTest(name=name):
                issues = webvtt.from_string(content).parse_issues
                self.assertEqual(len(issues), 1)
                with self.assertRaises(MalformedCaptionError) as cm:
                    webvtt.from_string(content, strict=True)
                self.assertEqual(str(issues[0]), str(cm.exception))

    def test_several_issues_in_order(self):
        vtt = webvtt.from_string(
            'WEBVTT\n\nstray\n\n00:00.000 --> 00:01.000\nok\n\n\n'
            '00:00.000 --> 00:99.000\nbad\n\nmore\ntext\n'
            )
        self.assertEqual(
            [(issue.line, issue.lines) for issue in vtt.parse_issues],
            [(3, ['stray']),
             (9, ['00:00.000 --> 00:99.000', 'bad']),
             (12, ['more', 'text'])]
            )

    def test_cue_with_identifier_is_located_at_the_identifier(self):
        vtt = webvtt.from_string(
            'WEBVTT\n\nid\n00:00.000 --> 00:99.000\nbad\n'
            )
        self.assertEqual(vtt.parse_issues[0].line, 3)

    def test_cue_read_without_empty_line_is_not_an_issue(self):
        vtt = webvtt.from_string(
            'WEBVTT\n\n00:00.000 --> 00:01.000\nok\n'
            '00:02.000 --> 00:99.000\nbad\n'
            )
        self.assertEqual(len(vtt), 1)
        self.assertEqual(vtt.parse_issues[0].line, 5)

    def test_dropped_cue_setting_is_not_an_issue(self):
        vtt = webvtt.from_string(
            'WEBVTT\n\n00:00.000 --> 00:01.000 unknown:a\nok\n'
            )
        self.assertEqual(len(vtt), 1)
        self.assertEqual(vtt.parse_issues, [])

    def test_from_buffer_and_read(self):
        content = 'WEBVTT\n\nstray\n'
        for name, vtt in (
                ('string', webvtt.from_buffer(io.StringIO(content))),
                ('bytes', webvtt.from_buffer(io.BytesIO(content.encode()))),
                ('lines', webvtt.from_buffer(['WEBVTT\n', '\n', 'stray\n']))):
            with self.subTest(name=name):
                self.assertEqual(vtt.parse_issues[0].line, 3)

        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td, 'in.vtt')
            path.write_bytes(b'\xef\xbb\xbfWEBVTT\r\n\r\nstray\r\n')
            vtt = webvtt.read(path)
        self.assertEqual(vtt.parse_issues[0].line, 3)
        self.assertEqual(vtt.parse_issues[0].lines, ['stray'])


class TestSRTParseIssues(unittest.TestCase):

    def parse(self, *lines):
        issues = []
        captions = srt.parse(list(lines), issues)
        return captions, [(issue.line, issue.message.split(' [')[0],
                           issue.lines) for issue in issues]

    def test_no_issues(self):
        captions, issues = self.parse(
            '1', '00:00:01,000 --> 00:00:02,000', 'one', '', 'more', '',
            '2', '00:00:03,000 --> 00:00:04,000', 'two'
            )
        self.assertEqual(len(captions), 2)
        self.assertEqual(issues, [])

    def test_issues_are_optional(self):
        self.assertEqual(
            len(srt.parse(['1', '00:00:01,000 --> 00:00:02,000', 'one'])),
            1
            )
        self.assertEqual(
            srt.parse_captions(['1', '00:00:01,000 --> 00:00:0x', 'one']),
            []
            )

    def test_invalid_timings(self):
        captions, issues = self.parse(
            '1', '00:00:01,000 --> 00:00:02,000', 'one', '',
            '2', '00:00:0x,000 --> 00:00:04,000', 'two'
            )
        self.assertEqual(len(captions), 1)
        self.assertEqual(
            issues,
            [(5, 'Invalid cue block',
              ['2', '00:00:0x,000 --> 00:00:04,000', 'two'])]
            )

    def test_timestamp_after_the_largest(self):
        _, issues = self.parse(
            '1', '00:00:01,000 --> 00:00:02,000', 'one', '',
            '2', '99999999999:00:00,000 --> 99999999999:00:01,000', 'two'
            )
        self.assertEqual(issues[0][:2], (5, 'Invalid cue block'))

    def test_text_after_a_skipped_cue(self):
        _, issues = self.parse(
            '1', '00:00:01,000 --> 00:00:02,000', 'one', '',
            '2', '00:00:0x,000 --> 00:00:04,000', 'two', '',
            'more text'
            )
        self.assertEqual(
            [issue[:2] for issue in issues],
            [(5, 'Invalid cue block'), (9, 'Invalid block')]
            )
        self.assertEqual(issues[1][2], ['more text'])

    def test_cue_without_text_in_order(self):
        captions, issues = self.parse(
            '1', '00:00:01,000 --> 00:00:02,000', '',
            '2', '00:00:0x,000 --> 00:00:04,000', 'two', '',
            '3', '00:00:05,000 --> 00:00:06,000', 'three'
            )
        self.assertEqual([c.text for c in captions], ['three'])
        self.assertEqual(
            [issue[:2] for issue in issues],
            [(1, 'Cue without text'), (4, 'Invalid cue block')]
            )

    def test_cue_with_text_after_an_empty_line_is_not_an_issue(self):
        captions, issues = self.parse(
            '1', '00:00:01,000 --> 00:00:02,000', '', 'late text'
            )
        self.assertEqual([c.text for c in captions], ['late text'])
        self.assertEqual(issues, [])

    def test_index_separated_from_the_timings(self):
        _, issues = self.parse(
            '1', '00:00:01,000 --> 00:00:02,000', 'one', '',
            '2', '', '00:00:0x,000 --> 00:00:04,000', 'two'
            )
        self.assertEqual(issues[0][0], 5)
        self.assertEqual(
            issues[0][2], ['2', '00:00:0x,000 --> 00:00:04,000', 'two']
            )

    def test_cue_without_empty_line_before_it(self):
        _, issues = self.parse(
            '1', '00:00:01,000 --> 00:00:02,000', 'one',
            '2', '00:00:0x,000 --> 00:00:04,000', 'two',
            '3', '00:00:05,000 --> 00:00:0x,000', 'three'
            )
        self.assertEqual([issue[0] for issue in issues], [4, 7])

    def test_from_srt_and_from_buffer(self):
        content = ('1\n00:00:01,000 --> 00:00:02,000\none\n\n'
                   '2\n00:00:0x,000 --> 00:00:04,000\ntwo\n')
        vtt = webvtt.from_buffer(io.StringIO(content), format='srt')
        self.assertEqual(vtt.parse_issues[0].line, 5)
        self.assertEqual(
            str(vtt.parse_issues[0]),
            "line 5: Invalid cue block "
            "['2', '00:00:0x,000 --> 00:00:04,000', 'two']"
            )

        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td, 'in.srt')
            path.write_text(content, encoding='utf-8')
            vtt = webvtt.from_srt(path)
        self.assertEqual(vtt.parse_issues[0].line, 5)


class TestSBVParseIssues(unittest.TestCase):

    def parse(self, *lines):
        issues = []
        captions = sbv.parse(list(lines), issues)
        return captions, [(issue.line, issue.message.split(' [')[0],
                           issue.lines) for issue in issues]

    def test_no_issues(self):
        captions, issues = self.parse(
            '0:00:01.000,0:00:02.000', 'one', '',
            '0:00:03.000,0:00:04.000', 'two'
            )
        self.assertEqual(len(captions), 2)
        self.assertEqual(issues, [])

    def test_issues_are_optional(self):
        self.assertEqual(
            len(sbv.parse(['0:00:01.000,0:00:02.000', 'one'])),
            1
            )

    def test_invalid_block(self):
        captions, issues = self.parse(
            '0:00:01.000,0:00:02.000', 'one', '', '', 'stray', 'text'
            )
        self.assertEqual(len(captions), 1)
        self.assertEqual(issues, [(5, 'Invalid block', ['stray', 'text'])])

    def test_cue_without_text(self):
        captions, issues = self.parse(
            '0:00:01.000,0:00:02.000', '',
            '0:00:03.000,0:00:04.000', 'two'
            )
        self.assertEqual([c.text for c in captions], ['two'])
        self.assertEqual(
            issues,
            [(1, 'Cue without text', ['0:00:01.000,0:00:02.000'])]
            )

    def test_timestamp_after_the_largest(self):
        captions, issues = self.parse(
            '99999999999:00:00.000,99999999999:00:01.000', 'one'
            )
        self.assertEqual(captions, [])
        self.assertEqual(issues[0][:2], (1, 'Invalid cue block'))

    def test_from_sbv_and_from_buffer(self):
        content = '0:00:01.000,0:00:02.000\none\n\nstray\n'
        vtt = webvtt.from_buffer(io.StringIO(content), format='sbv')
        self.assertEqual(str(vtt.parse_issues[0]),
                         "line 4: Invalid block ['stray']"
                         )

        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td, 'in.sbv')
            path.write_text(content, encoding='utf-8')
            vtt = webvtt.from_sbv(path)
        self.assertEqual(vtt.parse_issues[0].line, 4)
