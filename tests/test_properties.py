"""Property-based tests of reading, writing and editing the captions."""

import datetime
import re
import unittest

from hypothesis import given, settings, strategies as st

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

    # without captions the SRT file is empty, which is not read as SRT
    @untimed
    @given(st.lists(plain_captions, min_size=1))
    def test_vtt_to_srt_to_vtt(self, caption_list):
        vtt = webvtt.WebVTT(captions=caption_list)
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
    @given(st.text(st.sampled_from('<>/ab v.\t')))
    def test_text_strips_tags_like_regex(self, line):
        self.assertEqual(Caption(text=line).text,
                         re.sub('<.*?>', '', line))
