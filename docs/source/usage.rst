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

    # voice only reads a voice span at the start of the caption, voices
    # has the voice of every voice span in the text, in order
    caption = webvtt.Caption(text='<v Bob>Hi</v> <v Alice>Hello</v>')
    caption.voice   # 'Bob'
    caption.voices  # ['Bob', 'Alice']

    # the caption text is returned clean without cue tags,
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

    payload = requests.get('https://example.com/captions.vtt').text
    buffer = StringIO(payload)

    for caption in webvtt.from_buffer(buffer):
        print(caption.start)
        print(caption.end)
        print(caption.text)


Reading caption files from a binary file-like object
----------------------------------------------------

Binary data, such as a file opened in ``'rb'`` mode or a ``BytesIO`` object,
is decoded with the encoding of its Byte Order Mark, if any, or else with
``encoding``, UTF-8 by default. With a Byte Order Mark, saving keeps its
encoding and the Byte Order Mark, as when reading a file.

.. code-block:: python

    import webvtt
    from io import BytesIO

    with open('captions.vtt', 'rb') as f:
        vtt = webvtt.from_buffer(f)

    # formats supported: vtt, srt, sbv
    with open('captions.srt', 'rb') as f:
        vtt = webvtt.from_buffer(f, format='srt')

    # binary data in another encoding without a Byte Order Mark
    buffer = BytesIO('WEBVTT\n'.encode('latin-1'))
    vtt = webvtt.from_buffer(buffer, encoding='latin-1')

A string is not a file-like object and raises ``TypeError``: use
``from_string`` to read captions from a string.

The path of a file opened by name is kept in the ``file`` attribute, so
``save()`` without a path saves to it. A file-like object without a path,
such as standard input, a file opened from a file descriptor or a
``BytesIO`` object, gives captions without a file, as when creating
``WebVTT`` objects, so ``save()`` needs a path.


Reading captions from a string
------------------------------

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

Use ``format`` to read a string in SRT or SBV format:

.. code-block:: python

    import webvtt

    vtt = webvtt.from_string("""\
    1
    00:00:00,500 --> 00:00:07,000
    Caption #1
    """, format='srt')

    vtt = webvtt.from_string("""\
    0:00:00.500,0:00:07.000
    Caption #1
    """, format='sbv')


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

The times of the range can also be ``Timestamp`` objects, numbers of seconds
or ``timedelta`` objects, as in ``vtt.iter_slice(11, 27)``, and are rounded
to the nearest millisecond.

By default only the captions within the range are returned: a caption that
starts before ``start`` or ends after ``end`` is left out, even if part of it
is in the range. To cut the captions of a clip, ``overlapping`` also returns
those captions, and ``clip`` trims them to the range:

.. code-block:: python

    vtt = webvtt.WebVTT(captions=[
        webvtt.Caption('00:00:01.000', '00:00:05.000', 'first'),
        webvtt.Caption('00:00:03.000', '00:00:04.000', 'second'),
        ])
    start, end = '00:00:02.000', '00:00:06.000'

    [c.text for c in vtt.iter_slice(start, end)]
    # ['second']

    [c.text for c in vtt.iter_slice(start, end, overlapping=True)]
    # ['first', 'second']

    [c.start for c in vtt.iter_slice(start, end, overlapping=True, clip=True)]
    # ['00:00:02.000', '00:00:03.000']

A caption that only touches the range, ending at ``start`` or starting at
``end``, does not overlap it. With ``clip`` the captions returned are copies,
so neither trimming them nor later changes to them affect the captions of
``vtt``. The text of a copy is kept as it is, including any timestamp tags.
``clip`` needs ``overlapping``, and ``ValueError`` is raised without it, when
the iteration starts.

To save the captions of a clip, keep the styles and regions the captions may
use, and move the captions to the start of the clip:

.. code-block:: python

    clip = webvtt.WebVTT(
        captions=list(vtt.iter_slice(start, end, overlapping=True, clip=True)),
        styles=vtt.styles,
        regions=vtt.regions
        )
    clip.shift(-2)
    clip.save('clip.vtt')


Creating captions
-----------------

.. code-block:: python

    from datetime import timedelta

    from webvtt import WebVTT, Caption
    from webvtt.models import Timestamp

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

    # the times can also be Timestamp objects, numbers of seconds or
    # timedelta objects, rounded to the nearest millisecond
    caption = Caption(11.89, timedelta(seconds=15), 'Caption line 1')
    caption.end = Timestamp(0, 0, 16, 500)

    vtt.captions.append(caption)

    # save the captions to a file
    vtt.save('captions.vtt')

The lists given to ``WebVTT``, such as ``WebVTT(captions=captions)``, are
kept as its attributes, not copied, so changes to them show in the
instance. The list of lines given to a ``Caption`` or a ``Style`` is
copied.

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
read captions from a file.


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

    # or set its lines
    vtt[0].text = ['New caption text', 'on two lines']

    # delete a caption
    del vtt.captions[2]

The text of a caption is a string, split on its line breaks, or a sequence
of lines, as when creating a ``Caption``. Any other value raises
``TypeError``.


Comparing and copying captions
------------------------------

Captions, styles and regions are equal when they have the same content, and
``WebVTT`` instances when they have the same captions, styles, regions,
header text and metadata. Comments are not compared, nor where the captions
are saved, their encoding or the issues found when reading them:

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    vtt == webvtt.from_string(vtt.content)  # True
    vtt[0] == vtt[0].copy()                 # True

``copy`` returns a copy of a caption, or of all the captions, that shares
nothing with the original, so changing it leaves the original unchanged.
``copy.deepcopy`` works as ``copy``, while ``copy.copy`` shares what the
original has: the lines, times and settings of a caption, or the lists of
captions, styles and regions of a ``WebVTT``:

.. code-block:: python

    edited = vtt.copy()
    edited.shift(2)
    edited[0].text = 'New caption text'

    vtt[0].text  # unchanged


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

    # show the captions from 00:12:30 onwards 3 seconds later, the start
    # can also be a Timestamp, a number of seconds or a timedelta
    vtt.shift(3, start='00:12:30.000')

    # shift a single caption
    vtt[4].shift(0.25)

    # the offset can also be a timedelta
    vtt.shift(timedelta(minutes=1, seconds=30))

    vtt.save()

The offset is rounded to the nearest millisecond of its decimal value, with
halves rounded away from zero, so ``0.0005`` is 1 millisecond and ``-0.0005``
is -1 millisecond. A timestamp that would fall before zero is set to
``00:00:00.000``, so a caption moved entirely before the start is kept with
``00:00:00.000 --> 00:00:00.000`` timings, where it is never shown. To
remove those captions instead, as when cutting the start of the video, pass
``drop_before_zero``:

.. code-block:: python

    # cut the first 10 seconds, removing the captions that end within them
    vtt.shift(-10, drop_before_zero=True)

A caption that starts before zero but ends after it is kept, starting at
``00:00:00.000``. Only the captions that are shifted can be removed, so with
``start`` the captions before it stay.

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

A caption gives its times in milliseconds and its duration in seconds,
and ``total_length`` gives the time from the earliest start to the latest
end of the captions in seconds, with the milliseconds. Both are 0 instead
of negative for a caption that ends before it starts.

.. code-block:: python

    caption = webvtt.Caption('00:00:01.250', '00:00:03.000', 'Hello')
    caption.start_in_milliseconds  # 1250
    caption.end_in_milliseconds    # 3000
    caption.duration               # 1.75

    webvtt.WebVTT(captions=[caption]).total_length  # 1.75


Saving captions
---------------

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    # save to the same file
    vtt.save()

    # save to a different file
    vtt.save('new_captions.vtt')

    # save to a file path, the .vtt extension is added when it has none
    vtt.save('other/folder/new_captions')

    # save to a folder, keeping the name of the file that was read
    vtt.save('other/folder')

    # write to an open file
    with open('other_captions.vtt', 'w') as f:
        vtt.write(f)

Without a path, or with a folder, the name of the file that was read or
last saved is used. A file with the ``.vtt`` or ``.webvtt`` extension
keeps it, and any other extension is replaced by ``.vtt``, so captions
read from ``captions.srt`` are saved to ``captions.vtt``. ``save_as_srt()``
and ``save_as_sbv()`` do the same with ``.srt`` and ``.sbv``.


Retrieving captions as a string
-------------------------------

The captions can be retrieved as a string without an output file:

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    # print the content in WebVTT format
    print(vtt.content)

    # the same, and in the other formats
    print(vtt.to_string())
    print(vtt.to_string('srt'))
    print(vtt.to_string('srt', keep_formatting=True))
    print(vtt.to_string('sbv'))


Converting captions
-------------------

Captions can be read from the following formats:

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

Blank lines at the start of SRT and SBV files are skipped, and cues without
text are skipped, so a file whose first cue has no text is read. SRT cues
without an index are read, as most SRT players do, but the first cue of the
file needs one for the content to be read as SRT.

The colours and positions of SRT are read into WebVTT. A ``font`` tag with a
``color`` becomes a ``c`` tag with a class named from the colour, and a
``STYLE`` block gives each class its colour. Other ``font`` tags and
attributes, such as ``face`` and ``size``, are removed, keeping their text.
A ``{\an1}`` to ``{\an9}`` tag, which places the cue as the keys of a
numeric keypad, becomes the ``line`` and ``align`` cue settings, and is
removed from the text:

.. code-block:: python

    import webvtt

    vtt = webvtt.from_string("""\
    1
    00:00:00,500 --> 00:00:07,000
    {\\an8}<font color="#ff0000">Hello</font> world
    """, format='srt')

    print(vtt.content)
    # WEBVTT
    #
    # STYLE
    # ::cue(.color-ff0000) {
    #   color: #ff0000;
    # }
    #
    # 00:00:00.500 --> 00:00:07.000 line:0
    # <c.color-ff0000>Hello</c> world

Convert WebVTT captions to other formats:

* SubRip (.srt)
* YouTube SBV (.sbv)

.. code-block:: python

    import webvtt

    # save in SRT format
    vtt = webvtt.read('captions.vtt')
    vtt.save_as_srt()

    # write to an open file in SRT format
    with open('captions.srt', 'w') as f:
        vtt.write(f, format='srt')

    # the same for SBV format
    vtt.save_as_sbv()
    with open('captions.sbv', 'w') as f:
        vtt.write(f, format='sbv')

Captions without text, such as text of blank lines, are left out of the SRT
and SBV files, as these formats cannot have a cue without text, and the
others are numbered consecutively in SRT. The blank lines of the text are
also left out, as a blank line ends the cue. The cue tags are removed when
converting to SBV, which has no formatting.

The cue tags are removed when converting to SRT. To keep the formatting
instead, use ``keep_formatting``. Bold, italic, underline and ``font`` tags are
kept, and the cue classes with a ``color`` in the styles become ``font`` tags
with that color. Other cue tags are removed, keeping their text:

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

Only the ``color`` of ``::cue()`` selectors with a tag name, classes or both
is read, as in ``::cue(.loud)``, ``::cue(.loud.red)``, ``::cue(c.loud)`` or
``::cue(b)``, which colours every ``b`` tag. Class names can have any
character that WebVTT allows, written with CSS escapes where CSS needs them,
as in ``::cue(.c\+1)`` for ``<c.c+1>``. Other selectors, such as ``::cue``,
``::cue(#id)``, ``::cue([voice="Esme"])`` or ``::cue(c > b)``, are not read.
When more than one rule matches a cue tag, the rule with the most classes
applies, then one with a tag name, and then the one that comes last in the
styles, as in CSS.
Character references such as ``&lt;`` are written as they are.

The ``line`` and ``align`` cue settings are written to SRT as a ``{\anN}``
tag, with or without ``keep_formatting``, so captions read from SRT keep
their position. A line number from the top, or a percentage under a third,
places the cue at the top, a percentage up to two thirds in the middle, and
the cue is at the bottom otherwise. Only ``align:left`` and ``align:right``
are written, as the side of ``start`` and ``end`` depends on the direction of
the text, and no tag is written for a cue at the bottom center, where SRT
players place it, or with vertical text.

The ``encoding`` given to read a file without a Byte Order Mark is only
used for reading, as WebVTT files are UTF-8: ``save()`` writes UTF-8 unless
another encoding is given. SRT files have no fixed encoding, so captions
read with ``from_srt`` or ``from_buffer`` in SRT format and an
``encoding`` are saved by ``save_as_srt()`` in the same encoding:

.. code-block:: python

    import webvtt

    vtt = webvtt.from_srt('captions.srt', encoding='cp1252')

    # saved in cp1252
    vtt.save_as_srt('edited.srt')

    # saved in UTF-8, also for text that cp1252 cannot write
    vtt.save_as_srt('edited.srt', encoding='utf-8')

    # saved in UTF-8
    vtt.save()

``save_as_sbv()`` saves in UTF-8 unless another encoding is given, also for
captions read with ``from_sbv`` and an ``encoding``.

Saving text that the encoding cannot write raises ``UnicodeEncodeError``,
leaving an existing file unchanged.

A file with bytes that are not valid in its encoding raises
``UnicodeDecodeError`` when it is read. This is common with SRT files saved
in Windows-1252: read them with ``encoding='cp1252'``, or, when the encoding
is not known, give ``errors`` to ``read``, ``from_srt``, ``from_sbv`` or
``from_buffer``, as in ``bytes.decode``, to replace or drop those bytes:

.. code-block:: python

    import webvtt

    # invalid bytes are read as U+FFFD
    vtt = webvtt.from_srt('captions.srt', errors='replace')

    # invalid bytes are dropped
    vtt = webvtt.from_srt('captions.srt', errors='ignore')

    # keep the original file, as the bytes cannot be recovered
    vtt.save_as_srt('edited.srt')

Replaced or dropped bytes are lost for good, and ``save_as_srt()`` without an
output overwrites an SRT file that was read, so save to another path to keep
the original. With an ``encoding`` that cannot write U+FFFD, such as
``cp1252``, saving replaced bytes with ``save_as_srt()`` raises
``UnicodeEncodeError``: give ``encoding='utf-8'`` to save them.

An invalid byte in a timing line also affects the cue. With ``'replace'`` the
timing is not valid, so the cue is handled like any other with invalid timing:
ignored, or raising an error with strict parsing or in SBV format. With
``'ignore'`` the timing is read without the byte.

``from_buffer`` only uses ``errors`` for binary data. A file opened in text
mode decodes its own data, so give ``errors`` to ``open`` for it instead.


Segmenting captions for HLS
---------------------------

.. code-block:: python

    import webvtt

    # write 10-second segments and a prog_index.m3u8 playlist to output/path
    webvtt.segment('captions.vtt', 'output/path')

    # use 6-second segments and a different MPEG-TS value
    webvtt.segment('captions.vtt', 'other/path', seconds=6, mpegts=0)

    # segment captions already read, edited or from another format,
    # without saving them first
    vtt = webvtt.from_srt('captions.srt')
    vtt.change_framerate(25, 23.976)
    webvtt.segment(vtt, 'srt/path')

Every segment has the styles and regions of the captions, and the captions
in it keep their identifiers and cue settings. Comments are not written to
the segments. ``seconds`` is a whole number above zero and ``mpegts`` a
whole number from 0 to 8589934591.

Segmenting into a folder with the playlist or segments of an earlier run
raises ``FileExistsError``, so they are not replaced by mistake. Use
``overwrite=True`` to replace them, which also deletes the segments of the
earlier run that the new playlist does not have. Other files in the folder
are left alone:

.. code-block:: python

    # segment again into output/path, replacing the earlier segments
    webvtt.segment('captions.vtt', 'output/path', overwrite=True)

The playlist ends with the segment of the last caption, and every segment
lasts ``seconds``, as the length of the media is not known. Give it with
``duration``, as a timestamp, a number of seconds or a ``timedelta``, so the
playlist covers all the media, with empty segments after the last caption,
and its last segment ends with the media:

.. code-block:: python

    # a video of 1 minute 25.5 seconds: 9 segments, the last of 5.5 seconds
    webvtt.segment('captions.vtt', 'output/path', duration='00:01:25.500')

A caption starting at or after the end of the media raises ``ValueError``, as
the duration is likely wrong, and a caption ending after it is kept in the
last segment.

Segmentation is also available from the command line, see :doc:`cli`.


Files with Byte Order Mark (BOM)
--------------------------------

When the file has a BOM, saving it keeps the BOM and its encoding, also
when saving to SRT or SBV with ``save_as_srt()`` and ``save_as_sbv()``, which
take the same ``encoding`` and ``add_bom`` arguments as ``save()``:

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

Encoding names are matched as Python does, so ``UTF-8`` and ``utf8`` are
the same as ``utf-8``. The ``utf-8-sig``, ``utf-16`` and ``utf-32``
codecs always write a BOM, ``utf-16`` and ``utf-32`` in the byte order of
the platform, so ``add_bom=False`` raises ``ValueError`` with them: use
``utf-16-le``, ``utf-16-be``, ``utf-32-le`` or ``utf-32-be`` to choose the
byte order and whether to add a BOM. ``add_bom=True`` raises
``ValueError`` for an encoding without a BOM, such as ``latin-1``, while
the BOM of the file that was read is left out when saving in such an
encoding. When saving raises, an existing file is left unchanged.


WebVTT styles
-------------

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    for style in vtt.styles:
        print(style.text)

        # retrieve list of lines
        print(style.lines)

``STYLE`` blocks after the first cue are not styles as per the WebVTT
specification and are ignored, or raise ``MalformedCaptionError`` with
strict parsing.


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
``viewportanchor`` and ``scroll``. Setting a value that is not valid raises
``MalformedRegionError``, a subclass of ``MalformedCaptionError``, and the
settings are saved as they were read, including the ones that are not valid
or not known, with a setting per line. ``REGION`` blocks after the first cue
are not regions as per the WebVTT specification and are ignored, or raise
``MalformedRegionError`` with strict parsing. When converting to SRT, the
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

A block is a comment when it starts with ``NOTE`` followed by a space, a
tab or a line break. A block starting with other text, such as
``NOTEBOOK``, or containing ``-->`` is not a comment as per the WebVTT
specification, so it is ignored when reading, or raises
``MalformedCaptionError`` with strict parsing.


Handling errors
---------------

The errors raised by webvtt-py are available in the ``webvtt.errors``
module:

* ``MalformedFileError``: the content is not valid for the expected
  format (WebVTT, SRT or SBV).
* ``MalformedCaptionError``: a caption or cue setting is not valid, or the
  content does not pass strict parsing.
* ``MalformedRegionError``: a region setting is not valid, or a region does
  not pass strict parsing. It is a subclass of ``MalformedCaptionError``, so
  catching that error also catches it.
* ``MissingFilenameError``: captions are saved without an output path
  and there is no file to derive it from.

They all subclass ``WebVTTError``, so it catches any of them.
``MalformedFileError`` and ``MalformedCaptionError`` are also subclasses of
``ValueError``, like the other errors for values that are not valid, such
as text that could not be read back when saving. Those other errors are
the built-in ``ValueError`` and ``TypeError``, which ``WebVTTError`` does
not catch.

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
range ones such as ``00:00:61.000 --> 00:00:62.000`` is skipped. The blocks
that are skipped are kept in the ``parse_issues`` attribute as
``webvtt.ParseIssue`` objects, each with its line number, a message and its
lines, for WebVTT, SRT and SBV:

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    for issue in vtt.parse_issues:
        # line 42: Invalid cue block ['00:00.000 --> 00:0x.000', 'bad']
        print(issue)

        issue.line     # 42
        issue.message  # "Invalid cue block ['00:00.000 --> 00:0x.000', 'bad']"
        issue.lines    # ['00:00.000 --> 00:0x.000', 'bad']

Only whole blocks are recorded, including SRT and SBV cues without text.
Content dropped from a block that is still read, such as a cue setting that
is not valid, is not recorded. ``parse_issues`` is empty for captions that
were not read from a file, a buffer or a string.

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

The message of these errors starts with the line number of the block, or of
the cue timings line for a cue that is not separated by an empty line, as in
``line 42: Invalid cue block ['00:00.000 --> 00:0x.000', 'bad']``.

For region settings and regions after the first cue, the error is
``MalformedRegionError``, a subclass of ``MalformedCaptionError``.

Strict parsing also raises ``MalformedFileError``, also starting with the
line number, when ``WEBVTT`` is followed by text other than a space or a tab in the first line, such as
``WEBVTTX``, which the default parsing reads.

Strict parsing is only for WebVTT. SRT and SBV have no specification to
validate against, so ``from_buffer`` raises ``ValueError`` for ``strict=True``
with the ``srt`` or ``sbv`` format.

.. code-block:: python

    import webvtt
    from webvtt.errors import MalformedCaptionError

    try:
        vtt = webvtt.read('captions.vtt', strict=True)
    except MalformedCaptionError as e:
        print(f'captions.vtt is not valid WebVTT: {e}')


Validating and sorting captions
-------------------------------

Some problems are not found when reading, as each block is checked on its
own, and captions can also be changed or created in code. ``validate``
checks all the captions and returns the problems as
``webvtt.ValidationIssue`` objects, in the order of the captions:

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    for issue in vtt.validate():
        # caption 3: error: starts at 00:00:01.000, before caption 2, ...
        print(issue)

        issue.index     # 2, the index in vtt.captions
        issue.code      # 'order'
        issue.severity  # 'error'
        issue.message   # 'starts at 00:00:01.000, before caption 2, ...'

The errors are for captions that are not valid WebVTT:

* ``timing``: the end time is not after the start time
* ``order``: the caption starts before the previous one, as WebVTT requires
  the captions in order of start time
* ``region``: the ``region`` cue setting is a region that is not defined

The warnings are for captions that are valid WebVTT but likely have a
mistake:

* ``overlap``: the caption starts before an earlier one ends, so both are
  shown at the same time
* ``empty``: the caption has no text

In the messages, captions are numbered from 1, as in a file, while
``index`` is the index in ``captions``, from 0. The blocks skipped when
reading are in ``parse_issues`` instead, see `Strict parsing`_.

``validate`` does not repeat the checks of strict parsing, which are about
how the file is written, such as the header or cue settings that are not
valid. To check both, read the file with ``strict=True`` and then validate
the captions. The ``validate`` command of the CLI does both.

``sort`` puts the captions in order of start time, fixing the ``order``
errors. Captions that start at the same time keep their order:

.. code-block:: python

    vtt.sort()
    vtt.save()

Validating is also available from the command line, see :doc:`cli`.
