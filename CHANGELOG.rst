History
=======

Unreleased
----------

Changes that may need updates to the code using the library:

* Strict parsing raises ``MalformedCaptionError`` for cues whose end time is not after the start time, for blocks that are not a cue, comment, style or region, such as text without cue timings, for comments where ``NOTE`` is not followed by a space, a tab or a line break, or with ``-->``, and for styles after the first cue (#97, #133)
* Writing WebVTT raises ``ValueError`` for ``-->`` in a comment or in the header text, which WebVTT does not allow (#134, #135)
* ``NOTE`` blocks with ``-->`` are not read as comments, and header text with ``-->`` is read as empty, as WebVTT does, so the file can be saved again (#134, #135)

Changes:

* Fixed reading SRT files with whitespace around the first cue index, thanks to `@youdie006 <https://github.com/youdie006>`_ (#130)
* Fixed WebVTT styles ignored when ``STYLE`` is followed by whitespace (#133)
* Fixed WebVTT regions ignored after header text with ``-->`` (#135)
* Fixed non-ASCII digits read as numbers in timestamps and SRT cue indexes (#140)

0.6.0 (25-10-2026)
------------------

This is the last release supporting Python 3.7, 3.8 and 3.9.

Changes that may need updates to the code using the library:

* ``WebVTT`` takes keyword arguments only and does not read files, so ``WebVTT('captions.vtt')`` raises ``TypeError``: use ``webvtt.read`` to read captions from a file (#123)
* Writing WebVTT raises ``ValueError`` for text that could not be read back, such as an empty line or ``-->`` in the text of a caption (#122)
* Malformed cues are skipped when reading, instead of raising ``MalformedCaptionError``, unless ``strict=True`` (#93, #99)
* Timestamps are limited to ``9999999999:59:59.999``: cues past it are skipped when reading, and ``shift``, ``sync`` and ``change_framerate`` raise ``ValueError`` instead of moving captions past it (#119)
* The segment duration must be a whole number above zero, and the MPEG-TS value from 0 to 8589934591 (#125)

Changes:

* Added WebVTT regions (#108)
* Added cue settings to captions (#107)
* Added shift to captions, WebVTT and the CLI (#101)
* Added sync and change_framerate to WebVTT and the CLI (#102)
* Added Timestamp.from_seconds and Timestamp.in_milliseconds (#100)
* Added strict option to raise on malformed cue blocks (#93)
* Added keep_formatting to keep bold, italic, underline and the colours of the cue classes when saving SRT, thanks to `@darodi <https://github.com/darodi>`_ (#39, #118)
* Added manpage and documentation for the webvtt command (#95)
* Added py.typed marker for type checkers (#92)
* Added support for Python 3.13, 3.14 and 3.15, and tests on Windows and macOS (#84, #126)
* Improved parsing to follow the WebVTT spec for blocks (#98)
* Improved parsing to accept non-padded timestamps such as ``0:0:7.5``, as in Microsoft Teams transcripts, thanks to `@apetresc <https://github.com/apetresc>`_ (#45, #99)
* Improved writing to keep the header text and metadata (#103)
* Improved splitting text into lines to only break on CR, LF and CRLF (#104, #105)
* Improved reading of SRT cue timings to work as most SRT readers do (#114), and of SBV cue timings to carry over fields over their range (#115)
* Allowed more than two digits for timestamp hours, thanks to `@hlecnt <https://github.com/hlecnt>`_ (#80) and `@uzumakienes <https://github.com/uzumakienes>`_ for SBV (#111)
* Improved performance of Caption.text on long lines, thanks to `@BrianWillows <https://github.com/BrianWillows>`_ (#81), and of Caption.voice, thanks to `@uzumakienes <https://github.com/uzumakienes>`_ (#112)
* Improved segments to keep the styles, regions and identifiers of the captions (#125)
* Deprecated the file argument of WebVTT in favor of the file attribute (#123)
* Fixed reading buffers with a leading BOM, thanks to `@natesute <https://github.com/natesute>`_ (#82)
* Fixed the HLS playlist to use the configured segment duration, thanks to `@shkyyy18 <https://github.com/shkyyy18>`_ (#83)
* Fixed IndexError in slice_segments when the last caption ends on a segment boundary, thanks to `@t-hiroishi <https://github.com/t-hiroishi>`_ (#70), and when the captions are not sorted by end time, thanks to `@uzumakienes <https://github.com/uzumakienes>`_ (#110)
* Fixed SRT caption text lost after empty lines (#109) and after lines with only digits (#120)
* Fixed saving leaving an empty file when the captions cannot be encoded (#121)
* Fixed the API reference, the documentation of the exceptions and the examples (#90, #91, #127), and a docstring typo, thanks to `@Frenzie <https://github.com/Frenzie>`_ (#72)

0.5.1 (30-05-2024)
------------------

* Added voice span support (#55)
* Extended from_buffer support to allow BytesIO and also other format conversions (#32)
* Fixed save SRT to not include cue tags, thanks to `@lilaboc <https://github.com/lilaboc>`_ (#56)
* Fixed saved caption to include a line break after the last caption as per standard (#49)

0.5.0 (15-05-2024)
------------------

* Added styles support
* Added comments support
* Added from_string
* Added iterate over a slice of captions
* Refactor of the library
* Parser is no longer strict and ignores malformed blocks
* Improved BOM support allowing to keep the BOM or remove it
* Deprecated read_buffer in favor of from_buffer
* Removed support for old versions of Python: 3.4, 3.5 and 3.6

0.4.6 (18-11-2020)
------------------

* Add capability to get WebVTT formatted content without an output file, thanks to `@DawoudSheraz <https://github.com/DawoudSheraz>`_ (#34)
* Add Python 3.9 support

0.4.5 (09-04-2020)
------------------

* Fix issue reading buffer

0.4.4 (27-03-2020)
------------------

* Allow parsing empty SBV captions, thanks to `@ishunyu <https://github.com/ishunyu>`_ (#26)
* Fix invalid time cues, thanks to `@sontek <https://github.com/sontek>`_ (#19)
* Enable pytest as test runner, thanks to `@sontek <https://github.com/sontek>`_ (#20)
* Packaging improvements
* Added Python 3.8 support
* Improve parsing empty lines

0.4.3 (22-11-2019)
------------------

* Parsing improvements, thanks to `@sontek <https://github.com/sontek>`_ (#18)
* Add support for reading content from a file-like object, thanks to `@omerholz <https://github.com/omerholz>`_ (#23)
* Documentation fixes thanks to `@sontek <https://github.com/sontek>`_ (#22) and `@netcmcc <https://github.com/netcmcc>`_ (#24)

0.4.2 (08-06-2018)
------------------

* Renamed and reorganized few of the modules
* Parsing methods are now class methods: read, from_srt and from_sbv
* Improved usability with the addition of shortcuts to avoid instantiating the classes so we can do:

import webvtt

webvtt.read('captions.vtt')  # this will return a WebVTT instance


0.4.1 (24-12-2017)
------------------

* Support for saving cue identifiers

0.4.0 (18-09-2017)
------------------

The main goal of this release is a refactor of the WebVTT parser to be able to parse easier and give support to
new features of the format.

New features:

* Support for cue identifiers
* Support for parsing WebVTT captions with comments
* Support for parsing WebVTT captions with Style blocks
* Support for BOM in caption files
* Added method to write the captions to an opened file
* Convert WebVTT to SRT format
* Ignore empty captions in SRT format

Other:

* Refactored WebVTT parser

0.3.3 (23-08-2017)
------------------

The text for the caption is now returned clean (tags removed). The cue text could contain tags like:
* timestamp tags: *<00:19.000>*
* class tags: *<c.classname>text</c>*
* and others...
**Important**: It currently removes any tag present in the cue text. For example <b> would be removed.

Also a new attribute is available on captions to retrieve the text without cleaning tags: **raw_text**

0.3.2 (11-08-2017)
------------------

The goal of this release if to allow the WebVTT parser to be able to read caption files that contain metadata headers
that extend to more than one line.

0.3.1 (08-08-2017)
------------------

* Made hours in WebVTT parser optional as per specs.
* Added support to parse WebVTT files that contain metadata headers.

0.3.0 (02-06-2016)
------------------

New features:

* Added support for YouTube SBV captions.
* Added easy iteration to WebVTT class.
* New CLI command for segmenting captions for HLS.

Other:

* Improved parsers to reuse functionality.
* Added an exception for invalid timestamps in captions.
* Added an exception when saving without a filename.

0.2.0 (23-05-2016)
------------------

* Refactor of the main module and parsers.


0.1.0 (20-05-2016)
------------------

This module is released with the following initial features:

* Read/Edit/Write WebVTT captions.
* Read SRT captions and convert to WebVTT.
* Segment WebVTT files for captioning HLS video.
