History
=======

0.3.3 (23-08-2017) Hot fix on cue tags
--------------------------------------

The text for the caption is now returned clean (tags removed). The cue text could contain tags like:
* timestamp tags: *<00:19.000>*
* class tags: *<c.classname>text</c>*
* and others...
**Important**: It currently removes any tag present in the cue text. For example <b> would be removed.

Also a new attribute is available on captions to retrieve the text without cleaning tags: **raw_text**

0.3.2 (11-08-2017) Hot fix for compatibility
--------------------------------------------

The goal of this release if to allow the WebVTT parser to be able to read caption files that contain metadata headers
that extend to more than one line.

0.3.1 (08-08-2017) Compatibility updates
----------------------------------------

* Made hours in WebVTT parser optional as per specs.
* Added support to parse WebVTT files that contain metadata headers.

0.3.0 (02-06-2016) YouTube SBV
------------------------------

New features:

* Added support for YouTube SBV captions.
* Added easy iteration to WebVTT class.
* New CLI command for segmenting captions for HLS.

Other:

* Improved parsers to reuse functionality.
* Added an exception for invalid timestamps in captions.
* Added an exception when saving without a filename.

0.2.0 (23-05-2016) Module refactor
----------------------------------

* Refactor of the main module and parsers.


0.1.0 (20-05-2016) First release
--------------------------------

This module is released with the following initial features:

* Read/Edit/Write WebVTT captions.
* Read SRT captions and convert to WebVTT.
* Segment WebVTT files for captioning HLS video.
