.. This page is also the webvtt(1) manpage. After editing it, run
   ``make man`` to regenerate man/webvtt.1.

Command line
============

Synopsis
--------

::

    webvtt segment PATH -o OUTPUT [-d NUMBER] [-m NUMBER]
    webvtt shift PATH OFFSET [-o OUTPUT] [-s TIMESTAMP]
    webvtt sync PATH (-p FROM TO -p FROM TO ... | --fps FROM TO) [-o OUTPUT]
    webvtt -h

Description
-----------

``webvtt`` segments a WebVTT caption file for `HTTP Live Streaming`_ (HLS)
and shifts or synchronizes the timestamps of its captions.

``segment`` splits the captions in ``PATH`` into segments of a target duration. Each
segment is written to ``OUTPUT`` as ``fileSequenceN.webvtt``, where ``N`` is
the segment index starting at 0, along with a playlist named
``prog_index.m3u8`` that lists all the segments.

A caption whose time span crosses a segment boundary is included in every
segment it overlaps, so players display it regardless of which segment they
load. Every segment also has the ``STYLE`` and ``REGION`` blocks of ``PATH``,
which its captions use, and the captions keep their identifiers and cue
settings. Comments are not written to the segments.

Every segment starts with an ``X-TIMESTAMP-MAP`` header that maps the local
caption time ``00:00:00.000`` to an MPEG-TS presentation timestamp, so the
captions are kept in sync with the video stream.

.. _`HTTP Live Streaming`: https://datatracker.ietf.org/doc/html/draft-pantos-hls-rfc8216bis

``shift`` moves the captions in ``PATH`` earlier or later by ``OFFSET``
seconds. The offset is rounded to the nearest millisecond as written, with
halves rounded away from zero, so ``1.0005`` is 1001 milliseconds. A timestamp
that would fall before zero is set to ``00:00:00.000``, so a caption moved
entirely before the start is kept with ``00:00:00.000 --> 00:00:00.000``
timings. The shifted captions are written to standard output in UTF-8, or to
``OUTPUT`` when given.

``sync`` fixes captions that drift further out of sync along the video. With
``-p``, each point moves the time ``FROM`` in the captions to ``TO``; times
between two points are moved along the line between them, and times before
the first or after the last point along the line of the outermost points.
With ``--fps``, the timing is changed from one frame rate to another. Times
are rounded and set to zero like with ``shift``, and the output is written
the same way.

Commands
--------

``segment``
    Segment the WebVTT file at ``PATH``.

``shift``
    Shift the timestamps of the WebVTT file at ``PATH``.

``sync``
    Synchronize the timestamps of the WebVTT file at ``PATH``.

Options
-------

``-h``, ``--help``
    Show the help message and exit. Also available for each command, as in
    ``webvtt shift -h``.

Segment options
~~~~~~~~~~~~~~~

``-o OUTPUT``, ``--output OUTPUT``
    Directory where the segments and playlist are written. It is created if
    it does not exist. Existing files with the same names are overwritten.
    Required.

``-d NUMBER``, ``--target-duration NUMBER``
    Target duration of each segment in seconds, a whole number above zero.
    Also used for the ``#EXT-X-TARGETDURATION`` and ``#EXTINF`` values of
    the playlist. Default: ``10``.

``-m NUMBER``, ``--mpegts NUMBER``
    MPEG-TS value written to the ``X-TIMESTAMP-MAP`` header of each segment,
    a whole number from 0 to 8589934591, as MPEG-TS timestamps have 33
    bits. Default: ``900000`` (10 seconds at the 90 kHz MPEG-TS clock).

Shift options
~~~~~~~~~~~~~

``OFFSET``
    Number of seconds to shift the captions by, such as ``2`` or ``0.25``.
    Negative values move the captions earlier, as in ``-1.5``. Required.

``-o OUTPUT``, ``--output OUTPUT``
    File where the shifted captions are written, keeping the encoding and
    Byte Order Mark of the input file. It can be the input file itself to
    shift it in place. A ``.vtt`` extension is added if it has no
    extension, and if it is a directory the file is written there with the
    input file name.
    Default: standard output.

``-s TIMESTAMP``, ``--start TIMESTAMP``
    Only shift the captions starting at or after ``TIMESTAMP``, in
    ``[hh:]mm:ss.mmm`` format. Default: shift all the captions.

Sync options
~~~~~~~~~~~~

``-p FROM TO``, ``--point FROM TO``
    Move the time ``FROM`` in the captions to ``TO``. Each time is a
    timestamp in ``[hh:]mm:ss.mmm`` format or a number of seconds. Give it
    two or more times, in any order. Two points cannot have the same
    ``FROM``, and the ``TO`` times must be in the same order as the
    ``FROM`` times.

``--fps FROM TO``
    Change the timing from the frame rate ``FROM`` the captions are timed
    for to the frame rate ``TO`` of the video, such as ``25 23.976``. A frame
    rate can also be a ratio, such as ``24000/1001`` for the exact NTSC
    rate. Times are multiplied by ``FROM / TO``. Cannot be used with
    ``-p``.

``-o OUTPUT``, ``--output OUTPUT``
    File where the synchronized captions are written, as with ``shift``.
    Default: standard output.

Exit status
-----------

``0``
    The command completed successfully.

``1``
    The input file could not be read or is not a valid WebVTT file, or the
    output could not be written. An error message is printed to
    standard error, for example::

        webvtt: error: captions.vtt: not a valid WebVTT file

``2``
    Invalid command line arguments, such as an offset that is not a number,
    an invalid ``--start`` timestamp or sync points that cannot be used.

Examples
--------

Given ``captions.vtt``:

.. code-block:: text

    WEBVTT

    00:00:01.000 --> 00:00:04.000
    Hello and welcome.

    00:00:06.000 --> 00:00:12.000
    This caption spans two segments.

    00:00:14.500 --> 00:00:18.000
    Thanks for watching!

Segment it into 10 second segments:

::

    $ webvtt segment captions.vtt --output out
    $ ls out
    fileSequence0.webvtt  fileSequence1.webvtt  prog_index.m3u8

``out/prog_index.m3u8``:

.. code-block:: text

    #EXTM3U
    #EXT-X-TARGETDURATION:10
    #EXT-X-VERSION:3
    #EXT-X-PLAYLIST-TYPE:VOD
    #EXTINF:10.00000,
    fileSequence0.webvtt
    #EXTINF:10.00000,
    fileSequence1.webvtt
    #EXT-X-ENDLIST

``out/fileSequence0.webvtt``:

.. code-block:: text

    WEBVTT
    X-TIMESTAMP-MAP=MPEGTS:900000,LOCAL:00:00:00.000

    00:00:01.000 --> 00:00:04.000
    Hello and welcome.

    00:00:06.000 --> 00:00:12.000
    This caption spans two segments.

``out/fileSequence1.webvtt``:

.. code-block:: text

    WEBVTT
    X-TIMESTAMP-MAP=MPEGTS:900000,LOCAL:00:00:00.000

    00:00:06.000 --> 00:00:12.000
    This caption spans two segments.

    00:00:14.500 --> 00:00:18.000
    Thanks for watching!

Use 6 second segments and a different MPEG-TS value:

::

    $ webvtt segment captions.vtt -o out -d 6 -m 0

Show the captions 1.5 seconds earlier:

::

    $ webvtt shift captions.vtt -1.5
    WEBVTT

    00:00:00.000 --> 00:00:02.500
    Hello and welcome.

    00:00:04.500 --> 00:00:10.500
    This caption spans two segments.

    00:00:13.000 --> 00:00:16.500
    Thanks for watching!

Show the last caption 2 seconds later, updating the file in place:

::

    $ webvtt shift captions.vtt 2 --start 00:14.500 -o captions.vtt

Keep the first caption in place and move the last one from 00:14.500 to
00:15.850, synchronizing the captions in between:

::

    $ webvtt sync captions.vtt -p 00:01.000 00:01.000 -p 00:14.500 00:15.850
    WEBVTT

    00:00:01.000 --> 00:00:04.300
    Hello and welcome.

    00:00:06.500 --> 00:00:13.100
    This caption spans two segments.

    00:00:15.850 --> 00:00:19.700
    Thanks for watching!

Fix captions timed for a 25 fps video played with a 23.976 fps one,
updating the file in place:

::

    $ webvtt sync captions.vtt --fps 25 23.976 -o captions.vtt

See also
--------

The same segmentation, shifting and synchronizing are available from Python
with ``webvtt.segment()``, ``WebVTT.shift()``, ``WebVTT.sync()`` and
``WebVTT.change_framerate()``.
