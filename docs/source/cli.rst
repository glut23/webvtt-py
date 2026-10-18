.. This page is also the webvtt(1) manpage. After editing it, run
   ``make man`` to regenerate man/webvtt.1.

Command line
============

Synopsis
--------

::

    webvtt segment PATH -o OUTPUT [-d NUMBER] [-m NUMBER]
    webvtt shift PATH OFFSET [-o OUTPUT] [-s TIMESTAMP]
    webvtt -h

Description
-----------

``webvtt`` segments a WebVTT caption file for `HTTP Live Streaming`_ (HLS)
and shifts the timestamps of its captions.

``segment`` splits the captions in ``PATH`` into segments of a target duration. Each
segment is written to ``OUTPUT`` as ``fileSequenceN.webvtt``, where ``N`` is
the segment index starting at 0, along with a playlist named
``prog_index.m3u8`` that lists all the segments.

A caption whose time span crosses a segment boundary is included in every
segment it overlaps, so players display it regardless of which segment they
load.

Every segment starts with an ``X-TIMESTAMP-MAP`` header that maps the local
caption time ``00:00:00.000`` to an MPEG-TS presentation timestamp, so the
captions are kept in sync with the video stream.

.. _`HTTP Live Streaming`: https://datatracker.ietf.org/doc/html/draft-pantos-hls-rfc8216bis

``shift`` moves the captions in ``PATH`` earlier or later by ``OFFSET``
seconds. The offset is rounded to the nearest millisecond and a timestamp
that would fall before zero is set to ``00:00:00.000``, so a caption moved
entirely before the start is kept with ``00:00:00.000 --> 00:00:00.000``
timings. The shifted captions are written to standard output, or to
``OUTPUT`` when given.

Commands
--------

``segment``
    Segment the WebVTT file at ``PATH``.

``shift``
    Shift the timestamps of the WebVTT file at ``PATH``.

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
    Target duration of each segment in seconds. Also used for the
    ``#EXT-X-TARGETDURATION`` and ``#EXTINF`` values of the playlist.
    Default: ``10``.

``-m NUMBER``, ``--mpegts NUMBER``
    MPEG-TS value written to the ``X-TIMESTAMP-MAP`` header of each segment.
    Default: ``900000`` (10 seconds at the 90 kHz MPEG-TS clock).

Shift options
~~~~~~~~~~~~~

``OFFSET``
    Number of seconds to shift the captions by, such as ``2`` or ``0.25``.
    Negative values move the captions earlier, as in ``-1.5``. Required.

``-o OUTPUT``, ``--output OUTPUT``
    File where the shifted captions are written, keeping the encoding and
    Byte Order Mark of the input file. It can be the input file itself to
    shift it in place. A ``.vtt`` extension is added if missing, and if it
    is a directory the file is written there with the input file name.
    Default: standard output.

``-s TIMESTAMP``, ``--start TIMESTAMP``
    Only shift the captions starting at or after ``TIMESTAMP``, in
    ``[hh:]mm:ss.mmm`` format. Default: shift all the captions.

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
    Invalid command line arguments, such as an offset that is not a number
    or an invalid ``--start`` timestamp.

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

See also
--------

The same segmentation and shifting are available from Python with
``webvtt.segment()`` and ``WebVTT.shift()``.
