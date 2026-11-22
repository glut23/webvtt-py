"""Property-based tests of reading, writing and editing the captions."""

import datetime
import re
import unittest

from hypothesis import example, given, settings, strategies as st

import webvtt
from webvtt.errors import MalformedFileError
from webvtt.models import Caption, Style

# the examples are not timed, as their time varies by platform
untimed = settings(deadline=None)

FORMATS = st.sampled_from(('vtt', 'srt', 'sbv'))

# words with a meaning at the start of a block or a line
KEYWORDS = ('WEBVTT', 'NOTE', 'NOTE text', 'STYLE', 'REGION', '1')

# times up to 100 hours
times = st.integers(min_value=0, max_value=100 * 3600 * 1000 - 1).map(
    lambda milliseconds: datetime.timedelta(milliseconds=milliseconds)
    )


def lines(exclude=''):
    """
    Return the lines of text that can be written and read back.

    They have no line break, no ``-->``, which starts a new block, and are
    not only whitespace, which ends the text in SRT and SBV.
    """
    return st.sampled_from(KEYWORDS) | st.text(
        st.characters(exclude_categories=('Cs',),
                      exclude_characters='\r\n' + exclude),
        min_size=1
        ).filter(lambda text: '-->' not in text and text.strip())


cue_settings = st.lists(
    st.sampled_from((
        'line:0', 'line:10%,end', 'position:50%,center', 'size:80%',
        'align:start', 'align:left', 'vertical:rl', 'region:fred',
        )),
    unique=True
    ).map(' '.join)

captions = st.builds(
    Caption,
    times,
    times,
    st.lists(lines(), min_size=1, max_size=3),
    identifier=st.none() | lines(),
    settings=cue_settings
    )

# text without cue tags and SRT position tags, which are removed when
# converting to SRT
plain_captions = st.builds(
    Caption, times, times, st.lists(lines('<{'), min_size=1, max_size=3)
    )

vtts = st.builds(
    webvtt.WebVTT,
    captions=st.lists(captions),
    styles=st.lists(st.lists(lines(), min_size=1).map(Style), max_size=2),
    header_text=st.none() | lines(),
    metadata=st.lists(lines(), max_size=2),
    )

# lines that make the parser take most of its paths, mixed with any text
content_lines = st.sampled_from((
    '', ' ', 'WEBVTT', 'WEBVTT - title', 'WEBVTTX', '﻿WEBVTT', 'NOTE',
    'NOTE comment', 'NOTEBOOK', 'STYLE', 'REGION', '1', '-->',
    '00:00:01.000 --> 00:00:02.000', '00:01.000 --> 00:02.000 align:end',
    '00:00:02.000 --> 00:00:01.000', '00:00:61.000 --> 00:01:02.000',
    '00:00:01,000 --> 00:00:02,000', '0:0:1,5 --> 0:0:2,1500',
    '0:00:01.000,0:00:02.000', '{\\an8}text', '<v Bob>Hi</v>', '<b>bold',
    '<font color="#ff0000">red</font>', '::cue(.red) { color: red; }',
    'id:fred', 'width:40%', 'X-TIMESTAMP-MAP=MPEGTS:0,LOCAL:00:00:00.000',
    )) | st.text()

contents = st.builds(
    lambda lines, newline: newline.join(lines),
    st.lists(content_lines),
    st.sampled_from(('\n', '\r\n', '\r')),
    )


class TestParsing(unittest.TestCase):

    @untimed
    @given(contents, FORMATS)
    def test_lenient_parsing_only_raises_malformed_file_error(
            self, content, format
            ):
        try:
            webvtt.from_string(content, format=format)
        except MalformedFileError:
            pass


class TestRoundTrip(unittest.TestCase):

    @untimed
    @given(vtts)
    def test_write_and_read(self, vtt):
        self.assertEqual(webvtt.from_string(vtt.content), vtt)

    # Keep the input domain; choose WebVTT for text SRT cannot preserve.
    @untimed
    @given(caption_list=st.lists(plain_captions, min_size=1),
           expected_format=st.none())
    @example(caption_list=[Caption(text='&amp;lt;')], expected_format='srt')
    @example(caption_list=[Caption(text='&nbsp;')], expected_format='srt')
    @example(caption_list=[Caption(text='1\na --&gt; b')],
             expected_format='srt')
    @example(caption_list=[Caption(text='2 &lt; 3\n1\na --&gt; b')],
             expected_format='srt')
    @example(caption_list=[Caption(text='&lt;b&gt;literal&lt;/b&gt;')],
             expected_format='vtt')
    @example(caption_list=[Caption(text='1\n0:--&gt; b')],
             expected_format='vtt')
    def test_lossless_round_trip_uses_representable_format(
            self, caption_list, expected_format
            ):
        vtt = webvtt.WebVTT(captions=caption_list)
        literal_markup = re.compile(
            r'<(?:(?:b|i|u|font)(?=[ \t\n\f\r>])[^>]*|'
            r'/[ \t\n\f\r]*(?:b|i|u|font)[ \t\n\f\r]*)>',
            re.IGNORECASE | re.ASCII)
        # a line of digits followed by one that starts like cue timings
        # starts a new cue in SRT; whitespace in a line is any but a line
        # break, as in the SRT reader
        cue_start = re.compile(
            r'^[^\S\n]*[0-9]+[^\S\n]*\n[^\S\n]*[0-9]+:\S*[^\S\n]*-->',
            re.MULTILINE)
        requires_vtt = any(
            literal_markup.search(caption.text)
            or re.search(r'{\\an[1-9]}', caption.text)
            or '\r' in caption.text
            or cue_start.search(caption.text)
            or any(not line.strip(' \t\n\f\r')
                   for line in caption.text.split('\n'))
            for caption in vtt)
        selected_format = 'vtt' if requires_vtt else 'srt'
        if expected_format is not None:
            self.assertEqual(selected_format, expected_format)
        if selected_format == 'vtt':
            self.assertEqual(webvtt.from_string(vtt.to_string('vtt')), vtt)
            return
        srt = webvtt.from_string(vtt.to_string('srt'), format='srt')
        self.assertEqual(
            [(caption.start, caption.end, caption.text) for caption in srt],
            [(caption.start, caption.end, caption.text) for caption in vtt]
            )


class TestShift(unittest.TestCase):

    @untimed
    @given(st.lists(captions), st.data())
    def test_shift_and_back(self, caption_list, data):
        vtt = webvtt.WebVTT(captions=caption_list)
        earliest = min(
            (min(caption.start_time, caption.end_time).in_milliseconds()
             for caption in caption_list),
            default=0
            )
        # in seconds, rounded to the millisecond both ways, as a negative
        # offset rounds away from zero as a positive one does
        offset = data.draw(st.floats(min_value=-earliest / 1000,
                                     max_value=10 ** 6))
        original = vtt.copy()
        vtt.shift(offset)
        vtt.shift(-offset)
        self.assertEqual(vtt, original)


class TestText(unittest.TestCase):

    @untimed
    @given(st.lists(st.text(st.sampled_from('<>/ab v.\t')),
                    min_size=1, max_size=4))
    def test_text_strips_tags_like_regex(self, lines):
        caption = Caption(text=lines)
        self.assertEqual(
            caption.text,
            re.sub('<.*?>', '', caption.raw_text, flags=re.DOTALL)
            )

    @untimed
    @given(st.lists(st.text(st.sampled_from('<>/ab v.\t')),
                    min_size=1, max_size=4))
    def test_text_has_no_tags(self, lines):
        text = Caption(text=lines).text
        start = text.find('<')
        if start >= 0:
            self.assertNotIn('>', text[start:])
