History
=======

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
