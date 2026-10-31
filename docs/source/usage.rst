Usage
=====

Reading WebVTT caption files
----------------------------

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    # iterate over the captions
    for caption in vtt:
        print(caption.start)  # start timestamp in text format
        print(caption.end)  # end timestamp in text format
        print(caption.text)  # caption text
        print(caption.voice)  # voice span if present

    # iterate over the lines of a particular caption
    for line in vtt[0].lines:
        print(line)

    # the caption text is returned clean without class tags,
    # the raw text of a caption is available in raw_text
    vtt[0].text      # 'This is a caption text'
    vtt[0].raw_text  # 'This is a <c.colorE5E5E5>caption</c> text'

    # caption identifiers
    vtt[0].identifier  # 'chapter 1'


Reading WebVTT caption files from a file-like object
----------------------------------------------------

.. code-block:: python

    import webvtt
    import requests
    from io import StringIO

    payload = requests.get('http://subtitles.com/1234.vtt').text
    buffer = StringIO(payload)

    for caption in webvtt.from_buffer(buffer):
        print(caption.start)
        print(caption.end)
        print(caption.text)


Reading WebVTT caption files from a BytesIO object
--------------------------------------------------

.. code-block:: python

    import webvtt
    from io import BytesIO

    with open('captions.vtt', 'rb') as f:
        buffer = BytesIO(f.read())

    for caption in webvtt.from_buffer(buffer):
        print(caption.start)
        print(caption.end)
        print(caption.text)


Reading caption files in other formats from a BytesIO object
------------------------------------------------------------

.. code-block:: python

    import webvtt
    from io import BytesIO

    with open('captions.srt', 'rb') as f:
        buffer = BytesIO(f.read())

    # formats supported: vtt, srt, sbv
    for caption in webvtt.from_buffer(buffer, format='srt'):
        print(caption.start)
        print(caption.end)
        print(caption.text)


Reading WebVTT captions from a string
-------------------------------------

.. code-block:: python

    import webvtt
    import textwrap

    vtt = webvtt.from_string(textwrap.dedent("""
        WEBVTT

        00:00:00.500 --> 00:00:07.000
        Caption #1

        00:00:07.000 --> 00:00:11.890
        Caption #2 line 1
        Caption #2 line 2

        00:00:11.890 --> 00:00:16.320
        Caption #3
        """).strip()
        )

    for caption in vtt:
        print(caption.start)
        print(caption.end)
        print(caption.text)


Iterating over a slice of captions
----------------------------------

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')
    for caption in vtt.iter_slice(start='00:00:11.000',
                                  end='00:00:27.000'
                                  ):
        print(caption.start)
        print(caption.end)
        print(caption.text)

Only the captions within the range are returned: a caption that starts
before ``start`` or ends after ``end`` is left out, even if part of it is in
the range.


Creating captions
-----------------

.. code-block:: python

    from webvtt import WebVTT, Caption

    vtt = WebVTT()

    # creating a caption with a list of lines
    caption = Caption(
        '00:00:00.500',
        '00:00:07.000',
        ['Caption line 1', 'Caption line 2']
    )

    # an identifier can be assigned
    caption.identifier = 'chapter 1'

    # adding a caption
    vtt.captions.append(caption)

    # creating another caption with a text
    caption = Caption(
        '00:00:07.000',
        '00:00:11.890',
        'Caption line 1\nCaption line 2'
    )

    vtt.captions.append(caption)

    # save the captions to a file
    vtt.save('captions.vtt')

As in WebVTT, only CR, LF and CRLF break text into lines. Other characters
such as U+2028 or a form feed stay in the line.

Text that could not be read back from the file raises ``ValueError`` when
saving or writing the captions or getting their ``content``, and an existing
file is left unchanged:

* an empty line followed by more text, or ``-->``, in a caption or a style
* a line break or ``-->`` in an identifier
* an empty line followed by more text, or ``-->``, in a comment
* a line break or ``-->`` in the header text

A ``WebVTT`` object created from scratch has no filename, so ``save()``
requires an output path. Calling it without one raises
``MissingFilenameError``. The ``file`` attribute holds the path the
captions were read from or last saved to, and can be set to choose where
``save()`` writes:

.. code-block:: python

    import webvtt

    vtt = webvtt.from_srt('captions.srt')

    # save() would write captions.vtt, next to the file that was read
    vtt.file = 'new_captions.vtt'
    vtt.save()

``WebVTT`` takes keyword arguments only and does not read files, so
``WebVTT('captions.vtt')`` raises ``TypeError``: use ``webvtt.read()`` to
read captions from a file. The ``file`` argument of ``WebVTT`` is
deprecated in favor of the ``file`` attribute.


Manipulating captions
---------------------

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    # update start timestamp
    vtt[0].start = '00:00:01.250'

    # update end timestamp
    vtt[0].end = '00:00:03.890'

    # update caption text
    vtt[0].text = 'New caption text'

    # delete a caption
    del vtt.captions[2]


Cue settings
------------

The cue settings that follow the timestamps of a cue, such as
``line:0 align:start``, position and align the caption. They are available
as a ``CueSettings`` object in the ``settings`` attribute of a caption,
with a property for each setting that returns its value or ``None`` when it
is not set:

.. code-block:: python

    import webvtt
    from webvtt import Caption, CueSettings

    vtt = webvtt.read('captions.vtt')
    caption = vtt[0]

    caption.settings.line      # '10%,end'
    caption.settings.align     # 'start'
    str(caption.settings)      # 'line:10%,end align:start'

    # change, add or remove a setting
    caption.settings.line = '0'
    caption.settings.position = '50%,center'
    caption.settings.size = None

    # replace or clear all the settings
    caption.settings = 'line:0 align:start'
    caption.settings = None

    # create a caption with settings
    caption = Caption(
        '00:00:00.500',
        '00:00:07.000',
        'Caption text',
        settings=CueSettings(line='0', align='start')
    )

The supported settings are ``vertical``, ``line``, ``position``, ``size``,
``align`` and ``region``. Setting a value that is not valid as per the
WebVTT specification, such as ``align = 'middle'``, raises
``MalformedCaptionError``.

The settings are saved as they were read, in the same order and including
the ones that are not valid or not known, separated by a single space.
When a setting is not valid, such as ``align:middle`` from an older
version of the specification, its property returns ``None`` and assigning
a new value replaces it. When converting to SRT, the cue settings are not
included as the format does not support them.


Shifting captions
-----------------

Captions can be moved earlier or later by an offset, given as a number of
seconds or a ``timedelta``:

.. code-block:: python

    import webvtt
    from datetime import timedelta

    vtt = webvtt.read('captions.vtt')

    # show all the captions 1.5 seconds earlier
    vtt.shift(-1.5)

    # show the captions from 00:12:30 onwards 3 seconds later
    vtt.shift(3, start='00:12:30.000')

    # shift a single caption
    vtt[4].shift(0.25)

    # the offset can also be a timedelta
    vtt.shift(timedelta(minutes=1, seconds=30))

    vtt.save()

The offset is rounded to the nearest millisecond of its decimal value, with
halves
rounded away from zero, so ``0.0005`` is 1 millisecond and ``-0.0005`` is -1
millisecond. A timestamp that would fall before zero is set to
``00:00:00.000``, so a caption moved entirely before the start is kept with
``00:00:00.000 --> 00:00:00.000`` timings.

Shifting is also available from the command line, see :doc:`cli`.


Synchronizing captions
----------------------

When the captions are in sync at the start but drift further out of sync
over time, usually because they were timed for a video with a different
frame rate or cut, shifting is not enough. ``sync`` moves the captions to
two or more points, each a ``(from, to)`` pair where the time ``from`` in
the captions is moved to ``to``:

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    # the caption at 00:00:05.000 should be at 00:00:04.200 and the one at
    # 01:30:00.000 at 01:31:12.500, everything else is moved along
    vtt.sync(('00:00:05.000', '00:00:04.200'),
             ('01:30:00.000', '01:31:12.500'))

    # points can be taken from the captions themselves
    vtt.sync((vtt[0].start, '00:00:04.200'), (vtt[-1].start, '01:31:12.500'))

    # with more points, each part between two points is synchronized on its
    # own, for captions whose drift is not constant
    vtt.sync(('00:00:05.000', '00:00:04.200'),
             ('00:45:00.000', '00:45:30.000'),
             ('01:30:00.000', '01:31:12.500'))

    # captions timed for a 25 fps video played with a 23.976 fps one
    vtt.change_framerate(25, 23.976)

    # exact frame rates, like the NTSC 24000/1001, can be given as fractions
    from fractions import Fraction
    vtt.change_framerate(25, Fraction(24000, 1001))

    vtt.save()

The times of the points can be timestamp strings, ``Timestamp`` objects,
numbers of seconds or ``timedelta`` objects, and they can be given in any
order. Times between two points are moved along the line between them, and
times before the first or after the last point along the line of the
outermost points. Start and end times are both moved, so the duration of
the captions changes with the timing.

As with ``shift``, times are rounded to the nearest millisecond with halves
rounded away from zero, and a time that would fall before zero is set to
``00:00:00.000``. A ``ValueError`` is raised if fewer than two points are
given, two points have the same ``from`` time, or the ``to`` times are not
in the same order as the ``from`` times, since that would change the order
of the captions.

Use ``shift`` when all the captions are off by the same amount and ``sync``
when the difference grows along the video.

Synchronizing is also available from the command line, see :doc:`cli`.


Timestamps
----------

.. code-block:: python

    from webvtt.models import Timestamp

    # create a timestamp from a number of seconds, rounded to the
    # nearest millisecond with halves rounded away from zero
    str(Timestamp.from_seconds(5051.67))  # '01:24:11.670'

    # in_seconds leaves the milliseconds out
    Timestamp.from_string('01:24:11.670').in_seconds()       # 5051
    Timestamp.from_string('01:24:11.670').in_milliseconds()  # 5051670


Saving captions
---------------

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    # save to the same file
    vtt.save()

    # save to a different file
    vtt.save('new_captions.vtt')

    # save to a file path, the .vtt extension is added when missing
    vtt.save('other/folder/new_captions')

    # save to a folder, keeping the name of the file that was read
    vtt.save('other/folder')

    # write to an open file
    with open('other_captions.vtt', 'w') as f:
        vtt.write(f)


Retrieving WebVTT formatted captions
------------------------------------

WebVTT content can be retrieved without an output file:

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    # print the content in WebVTT format
    print(vtt.content)


Converting captions
-------------------

You can read captions from the following formats:

* SubRip (.srt)
* YouTube SBV (.sbv)

.. code-block:: python

    import webvtt

    # read captions from SRT format
    vtt = webvtt.from_srt('captions.srt')

    # save the captions in WebVTT format
    vtt.save()

    # the conversion can be done by chaining the method calls
    webvtt.from_srt('captions.srt').save()

    # the same for SBV format
    vtt = webvtt.from_sbv('captions.sbv')

Some SRT files have empty lines in the caption text. When reading SRT, a new
caption starts at a cue index followed by the cue timings, even without an
empty line before it. Any other text after an empty line stays in the
current caption, and the empty lines are removed.

The cue timings of SRT are read as in most SRT readers. The separator before
the milliseconds can be a comma or a dot, the fields can be shorter, as in
``0:0:7,500``, and the milliseconds are read as a number, so ``00:00:07,5``
is 5 milliseconds. A field over its range carries over, so ``00:00:07,1500``
is read as ``00:00:08.500``. The hours and the milliseconds are required, and
a cue without them is skipped. The cue timings of SBV carry over in the same
way, so ``0:61:00.000`` is read as ``01:01:00.000``.

Convert WebVTT captions to other formats:

* SubRip (.srt)

.. code-block:: python

    import webvtt

    # save in SRT format
    vtt = webvtt.read('captions.vtt')
    vtt.save_as_srt()

    # write to an open file in SRT format
    with open('captions.srt', 'w') as f:
        vtt.write(f, format='srt')

The cue tags are removed when converting to SRT. To keep the formatting
instead, use ``keep_formatting``. Bold, italic, underline and ``font`` tags are
kept, and the cue classes with a ``color`` in the styles become ``font`` tags
with that colour. Other cue tags are removed, keeping their text:

.. code-block:: python

    import webvtt

    vtt = webvtt.from_string("""\
    WEBVTT

    STYLE
    ::cue(.magenta) {
      color: #ff00ff;
    }

    00:00:00.500 --> 00:00:07.000
    <c.magenta><i>Hello</i> world</c>
    """)
    vtt.save_as_srt('captions.srt', keep_formatting=True)

    # the caption is saved as:
    # <font color="#ff00ff"><i>Hello</i> world</font>

Only the ``color`` of ``::cue(.class)`` selectors is read. When a cue has more
than one class with a colour, the rule that comes last in the styles applies.
Character references such as ``&lt;`` are written as they are.


Segmenting captions for HLS
---------------------------

.. code-block:: python

    import webvtt

    # write 10-second segments and a prog_index.m3u8 playlist to output/path
    webvtt.segment('captions.vtt', 'output/path')

    # use 6-second segments and a different MPEG-TS value
    webvtt.segment('captions.vtt', 'output/path', seconds=6, mpegts=0)

Every segment has the styles and regions of the file, and the captions keep
their identifiers and cue settings. Comments are not written to the
segments. ``seconds`` is a whole number above zero and ``mpegts`` a whole
number from 0 to 8589934591.

Segmentation is also available from the command line, see :doc:`cli`.


WebVTT files with Byte Order Mark (BOM)
---------------------------------------

When the WebVTT file has a BOM, saving it keeps the BOM:

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions_with_bom.vtt')

    # saved file keeps the BOM
    vtt.save()


Add a BOM to a file without it:

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions_without_bom.vtt')

    # saved file has a BOM
    vtt.save(add_bom=True)


Remove the BOM from a file:

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions_with_bom.vtt')

    # saved file does not have a BOM
    vtt.save(add_bom=False)


Save a file with a different encoding:

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    vtt.save(encoding='utf-32-le')

    # save in a different encoding with a BOM
    vtt.save(encoding='utf-32-le',
             add_bom=True
             )


WebVTT styles
-------------

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    for style in vtt.styles:
        print(style.text)

        # retrieve list of lines
        print(style.lines)


Adding styles:

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    vtt.styles.append(
        webvtt.Style('::cue(b) {\n  color: peachpuff;\n}')
        )
    # list of lines is supported
    vtt.styles.append(
        webvtt.Style(['::cue(b) {',
                      '  color: peachpuff;',
                      '}'
                      ])
        )


Updating styles:

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    vtt.styles[0].lines[1] = '  color: papayawhip;'


WebVTT regions
--------------

Regions are areas of the video where captions are rendered, defined in
``REGION`` blocks before the first cue and used by the captions through
the ``region`` cue setting. They are available in the ``regions`` list as
``Region`` objects, with a property for each setting that returns its
value or ``None`` when it is not set:

.. code-block:: python

    import webvtt
    from webvtt import Region

    vtt = webvtt.read('captions.vtt')

    for region in vtt.regions:
        print(region.id, region.width, region.lines)

    # change a region
    vtt.regions[0].width = '50%'
    vtt.regions[0].scroll = None

    # add a region and use it in a caption
    vtt.regions.append(
        Region(
            id='fred',
            width='40%',
            lines='3',
            regionanchor='0%,100%',
            viewportanchor='10%,90%',
            scroll='up'
        )
    )
    vtt.captions[0].settings.region = 'fred'

The supported settings are ``id``, ``width``, ``lines``, ``regionanchor``,
``viewportanchor`` and ``scroll``. As with cue settings, setting a value
that is not valid raises ``MalformedCaptionError``, and the settings are
saved as they were read, including the ones that are not valid or not
known, with a setting per line. ``REGION`` blocks after the first cue are
not regions as per the WebVTT specification and are ignored, or raise
``MalformedCaptionError`` with strict parsing. When converting to SRT, the
regions are not included.

Removing or renaming a region does not update the captions that use it.


WebVTT header
-------------

The text following ``WEBVTT`` in the first line and the metadata lines
after it, such as the ``X-TIMESTAMP-MAP`` used by HLS, are kept when
reading and written back when saving:

.. code-block:: text

    WEBVTT - Sample title
    X-TIMESTAMP-MAP=LOCAL:00:00:00.000,MPEGTS:126000
    Kind: captions

    00:00:00.500 --> 00:00:07.000
    Caption text #1

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    vtt.header_text  # '- Sample title'

    vtt.metadata
    # ['X-TIMESTAMP-MAP=LOCAL:00:00:00.000,MPEGTS:126000', 'Kind: captions']

    vtt.metadata.append('Language: en')

Metadata lines are kept as they are, in order. Shifting or synchronizing the
captions does not change them, so ``X-TIMESTAMP-MAP`` keeps mapping the file
to the same media time. Saving, writing or getting the ``content`` raises
``ValueError`` if the header text has a line break or contains ``-->``, or if
a metadata line is empty, has a line break or contains ``-->``, since that
would break the file. Header text with ``-->`` is not valid WebVTT and is
read as empty, or raises ``MalformedCaptionError`` with strict parsing.


WebVTT comments
---------------

Comments can be added to or retrieved from different items:

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    # comments from the top of the file
    print(vtt.header_comments)

    # comments from the bottom of the file
    print(vtt.footer_comments)

    # comments in a style
    print(vtt.styles[0].comments)

    # comments in a caption
    print(vtt.captions[0].comments)

    # comments are just a list of strings
    vtt.captions[5].comments.append('caption for review')

A ``NOTE`` block containing ``-->`` is not a comment as per the WebVTT
specification, so it is ignored when reading, or raises
``MalformedCaptionError`` with strict parsing.


Handling errors
---------------

The errors raised by webvtt-py are available in the ``webvtt.errors``
module:

* ``MalformedFileError``: the content is not valid for the expected
  format (WebVTT, SRT or SBV).
* ``MalformedCaptionError``: a caption, cue setting or region is not
  valid, or the content does not pass strict parsing.
* ``MissingFilenameError``: captions are saved without an output path
  and there is no file to derive it from.

.. code-block:: python

    import webvtt
    from webvtt.errors import (
        MalformedFileError,
        MalformedCaptionError,
        MissingFilenameError
    )

    try:
        vtt = webvtt.read('captions.vtt')
    except MalformedFileError:
        print('captions.vtt is not a valid WebVTT file')
    except MalformedCaptionError as e:
        print(f'captions.vtt has an invalid caption: {e}')

    # an instance not read from a file needs an output path
    vtt = webvtt.WebVTT()
    try:
        vtt.save()
    except MissingFilenameError:
        vtt.save('captions.vtt')


Parsing rules
-------------

The WebVTT parser follows the parsing rules of the WebVTT specification:
blocks are separated by empty lines, so lines containing only whitespace
are part of the cue text, and a line containing ``-->`` starts a new
block when it is not the timings line of the current one. Cues without
text are kept as captions with empty text.

Timestamps with fields shorter than the specification requires, such as
``0:0:13.540`` in Microsoft Teams transcripts or ``0:1:5.2``, are accepted
and the captions are saved in the standard ``00:00:13.540`` and
``00:01:05.200`` format. The fraction of a second is padded on the right,
so ``.2`` is read as 200 milliseconds.


Strict parsing
--------------

By default the parser ignores blocks it cannot parse, so a cue with
malformed timings such as ``00:00:00.-004 --> 00:00:04.300`` or out of
range ones such as ``00:00:61.000 --> 00:00:62.000`` is skipped.
To validate the content, pass ``strict=True`` to ``read``,
``from_buffer`` or ``from_string`` and a ``MalformedCaptionError`` is
raised instead. Strict parsing also raises the error for:

* timestamps that are not in the WebVTT format
* cues whose end time is not after the start time
* cue and region settings that are not known, not valid or repeated
* blocks after the header that are not a cue, comment, style or region,
  such as text without cue timings, or a comment that does not start with
  ``NOTE`` followed by a space, a tab or a line break, or contains ``-->``
* styles and regions after the first cue
* a cue that is not separated from the previous cue, comment or style by
  an empty line

.. code-block:: python

    import webvtt
    from webvtt.errors import MalformedCaptionError

    try:
        vtt = webvtt.read('captions.vtt', strict=True)
    except MalformedCaptionError as e:
        print(f'captions.vtt is not valid WebVTT: {e}')
