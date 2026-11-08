.. This page is also the webvtt(1) manpage. After editing it, run
   ``make man`` to regenerate man/webvtt.1.

Command line
============

Synopsis
--------

::

    webvtt segment PATH -o OUTPUT [-d NUMBER] [-m NUMBER] [--duration TIME]
                   [--overwrite] [INPUT OPTIONS]
    webvtt shift PATH OFFSET [-o OUTPUT] [-s TIME] [--drop-before-zero]
                 [INPUT OPTIONS]
    webvtt sync PATH (-p FROM TO -p FROM TO ... | --fps FROM TO) [-o OUTPUT]
                [INPUT OPTIONS]
    webvtt validate PATH [INPUT OPTIONS]
    webvtt convert PATH [-o OUTPUT] [-t FORMAT] [--keep-formatting]
                   [INPUT OPTIONS]
    webvtt -h
    webvtt --version

Description
-----------

``webvtt`` segments a caption file for `HTTP Live Streaming`_ (HLS),
shifts or synchronizes the timestamps of its captions, checks it for
problems, or converts it to another format. The file can be WebVTT, SRT or
SBV, read in the format of its extension: ``.srt`` for SRT, ``.sbv`` for SBV
and any other for WebVTT, unless ``--format`` is given.

``segment`` splits the captions in ``PATH`` into segments of a target
duration. Each segment is written to ``OUTPUT`` as ``fileSequenceN.webvtt``,
where ``N`` is the segment index starting at 0, along with a playlist named
``prog_index.m3u8`` that lists all the segments. An ``OUTPUT`` with the
playlist or segments of an earlier run is an error, unless ``--overwrite`` is
given.

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
timings, unless ``--drop-before-zero`` is given to remove it. The shifted
captions are written to standard output in UTF-8, or to ``OUTPUT`` when given,
in the format of the input, or of the extension of ``OUTPUT`` when it is
``.vtt``, ``.webvtt``, ``.srt`` or ``.sbv``. The formatting of the cue text
is kept when writing SRT.

``sync`` fixes captions that drift further out of sync along the video. With
``-p``, each point moves the time ``FROM`` in the captions to ``TO``; times
between two points are moved along the line between them, and times before
the first or after the last point along the line of the outermost points.
With ``--fps``, the timing is changed from one frame rate to another. Times
are rounded and set to zero like with ``shift``, and the output is written
the same way.

``validate`` checks the captions in ``PATH`` and prints each problem on its
own line, as ``PATH: line N: error: MESSAGE`` for a block skipped when
reading the file, or ``PATH: caption N: SEVERITY: MESSAGE`` for a caption,
numbered from 1. Captions out of order, not ending after they start or in a
region that is not defined are errors, as they are not valid WebVTT.
Captions that overlap an earlier one or have no text are warnings. When
there is no other error, a WebVTT file is also read with strict parsing,
which finds other problems such as cue settings that are not valid, and its
first error is printed as ``PATH: line N: error: MESSAGE``. Nothing is
printed when there is no problem.

``convert`` writes the captions in ``PATH`` in the format given with ``-t``,
or else in the format of the extension of ``OUTPUT``, or else as WebVTT, to
standard output in UTF-8 or to ``OUTPUT``. Reading SRT turns its ``font``
colours into cue classes with a ``STYLE`` block and its ``{\anN}``
positions into cue settings, and writing SRT writes the positions back.

The commands can also be run as ``python -m webvtt``, as in
``python -m webvtt shift captions.vtt 2``.

The commands read the captions from standard input when ``PATH`` is ``-``,
as WebVTT unless ``--format`` is given and decoded as UTF-8 unless
``--encoding`` is given, so they can be used in pipes. A file named ``-`` can
be read as ``./-``.

Commands
--------

``segment``
    Segment the captions at ``PATH`` into WebVTT segments.

``shift``
    Shift the timestamps of the captions at ``PATH``.

``sync``
    Synchronize the timestamps of the captions at ``PATH``.

``validate``
    Check the captions at ``PATH`` for problems.

``convert``
    Convert the captions at ``PATH`` to another format.

Options
-------

``-h``, ``--help``
    Show the help message and exit. Also available for each command, as in
    ``webvtt shift -h``.

``--version``
    Show the version of webvtt-py and exit.

Input options
~~~~~~~~~~~~~

These options are available for every command.

``-f FORMAT``, ``--format FORMAT``
    Format of the captions at ``PATH``: ``vtt``, ``srt`` or ``sbv``.
    Default: from the extension of ``PATH``, ``.srt`` for ``srt``, ``.sbv``
    for ``sbv`` and any other for ``vtt``, or ``vtt`` for standard input.

``--encoding ENCODING``
    Encoding of an input without a Byte Order Mark, such as ``cp1252``. The
    Byte Order Mark is used when there is one. Writing SRT to a file keeps
    this encoding, while WebVTT and SBV are written in UTF-8. Default:
    ``utf-8``.

Segment options
~~~~~~~~~~~~~~~

``-o OUTPUT``, ``--output OUTPUT``
    Directory where the segments and playlist are written. It is created if
    it does not exist. Required.

``-d NUMBER``, ``--target-duration NUMBER``
    Target duration of each segment in seconds, a whole number above zero.
    Also used for the ``#EXT-X-TARGETDURATION`` value of the playlist and the
    ``#EXTINF`` of its segments, except the last with ``--duration``.
    Default: ``10``.

``-m NUMBER``, ``--mpegts NUMBER``
    MPEG-TS value written to the ``X-TIMESTAMP-MAP`` header of each segment,
    a whole number from 0 to 8589934591, as MPEG-TS timestamps have 33
    bits. Default: ``900000`` (10 seconds at the 90 kHz MPEG-TS clock).

``--duration TIME``
    Length of the media, as a timestamp such as ``01:25.500`` or a number of
    seconds such as ``85.5``. The playlist then covers all the media, with
    empty segments after the last caption, and the ``#EXTINF`` of its last
    segment ends with the media. A caption starting at or after it is an
    error. Without it, the playlist ends with the segment of the last
    caption, and every segment lasts the target duration.

``--overwrite``
    Replace the playlist and segments of an earlier run in ``OUTPUT``, and
    delete the segments of that run that the new playlist does not have.
    Other files in ``OUTPUT`` are left alone. Without it, an ``OUTPUT`` with
    a ``prog_index.m3u8`` or ``fileSequenceN.webvtt`` file is an error.

Shift options
~~~~~~~~~~~~~

``OFFSET``
    Number of seconds to shift the captions by, such as ``2`` or ``0.25``.
    Negative values move the captions earlier, as in ``-1.5``. Required.

``-o OUTPUT``, ``--output OUTPUT``
    File where the shifted captions are written, keeping the encoding and
    Byte Order Mark of the input file. It can be the input file itself to
    shift it in place. The captions are written in the format of its
    extension when it is ``.vtt``, ``.webvtt``, ``.srt`` or ``.sbv``, and
    else in the format of the input, whose extension is added if it has no
    extension. If it is a directory, the file is written there with the
    input file name, which is an error when reading standard input.
    Default: standard output.

``-s TIME``, ``--start TIME``
    Only shift the captions starting at or after ``TIME``, a timestamp in
    ``[hh:]mm:ss.mmm`` format or a number of seconds, such as ``47.5``.
    Default: shift all the captions.

``--drop-before-zero``
    Remove the shifted captions that end at or before ``00:00:00.000``, as
    they are never shown. A caption that starts before zero but ends after
    it is kept, starting at ``00:00:00.000``. Without it, those captions are
    kept with ``00:00:00.000 --> 00:00:00.000`` timings.

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

Convert options
~~~~~~~~~~~~~~~

``-o OUTPUT``, ``--output OUTPUT``
    File where the converted captions are written, as with ``shift``, with
    the extension of the output format added if it has no extension.
    Default: standard output.

``-t FORMAT``, ``--to FORMAT``
    Format of the output: ``vtt``, ``srt`` or ``sbv``. Default: the format
    of the extension of ``OUTPUT``, or ``vtt``.

``--keep-formatting``
    When writing SRT, keep bold, italic and underline, and write the colours
    of the cue classes in the styles as ``font`` tags, instead of removing
    the cue tags. SBV has no formatting.

Exit status
-----------

``0``
    The command completed successfully. For ``validate``, the file has no
    errors, though it can have warnings.

``1``
    The input could not be read or is not valid in its format, the captions
    could not be moved as asked, or the output could not be written. For
    ``segment``, it is also an error when the output directory has the files
    of an earlier run without ``--overwrite``, or when a caption starts at or
    after ``--duration``. An error message is printed to standard error, for
    example::

        webvtt: error: captions.vtt: not a valid WebVTT file

For ``validate``, ``1`` is also the status when the file has errors, which
are printed to standard output.

``2``
    Invalid command line arguments, such as an offset that is not a number,
    an invalid ``--start`` time, sync points that cannot be used, or an
    unknown format or encoding.

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

Segment it into 10-second segments:

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

Segment it again into ``out``, with 6-second segments and a different
MPEG-TS value, replacing the earlier segments:

::

    $ webvtt segment captions.vtt -o out
    webvtt: error: out: has the files of an earlier segmentation, such as fileSequence0.webvtt; use --overwrite to replace them
    $ webvtt segment captions.vtt -o out -d 6 -m 0 --overwrite

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

Cut the first 5 seconds of the video, removing the first caption, which
would end before the start:

::

    $ webvtt shift captions.vtt -5 --drop-before-zero
    WEBVTT

    00:00:01.000 --> 00:00:07.000
    This caption spans two segments.

    00:00:09.500 --> 00:00:13.000
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

Shift and synchronize the captions in a pipe, reading them from standard
input:

::

    $ webvtt shift captions.vtt 2 | webvtt sync - --fps 25 23.976 > fixed.vtt

Synchronize the captions and segment them, without a file in between:

::

    $ webvtt sync captions.vtt --fps 25 23.976 | webvtt segment - -o out

Check ``captions.vtt``, which has no problems, so nothing is printed:

::

    $ webvtt validate captions.vtt

Check ``edited.vtt``, where the captions are out of order, the last one is
in a region that is not defined and overlaps the first one, and a block is
not a cue:

::

    $ webvtt validate edited.vtt
    edited.vtt: line 12: error: Invalid block ['NOTEBOOK']
    edited.vtt: caption 2: error: starts at 00:00:01.000, before caption 1, which starts at 00:00:06.000
    edited.vtt: caption 3: error: is in the region 'bottom', which is not defined
    edited.vtt: caption 3: warning: starts at 00:00:11.000, before caption 1 ends at 00:00:12.000

Shift SRT captions, keeping them in SRT, and convert them to WebVTT:

::

    $ webvtt shift captions.srt 2 -o captions.srt
    $ webvtt convert captions.srt -o captions.vtt

Convert WebVTT to SRT, keeping the formatting, and read an SRT file in
Windows-1252 from standard input:

::

    $ webvtt convert captions.vtt -o captions.srt --keep-formatting
    $ cat old.srt | webvtt convert - -f srt --encoding cp1252 > new.vtt

See also
--------

The same segmentation, shifting, synchronizing, validation and conversion
are available from Python with ``webvtt.segment()``, ``WebVTT.shift()``,
``WebVTT.sync()``, ``WebVTT.change_framerate()``, ``WebVTT.validate()``,
``webvtt.from_srt()``, ``webvtt.from_sbv()``, ``WebVTT.save_as_srt()`` and
``WebVTT.save_as_sbv()``, and ``WebVTT.sort()`` puts the captions in order
of start time.
