History
=======

0.4.6
------------------

* Add capability to get WebVTT formatted content without an output file

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
