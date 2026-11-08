webvtt-py
=========

|pypi| |pyversions| |license| |coverage| |build-status| |docs-status| |downloads|

``webvtt-py`` is a Python library for reading, writing and converting WebVTT_ caption files. It also features caption segmentation useful when captioning `HLS videos`_.

Documentation is available at https://webvtt-py.readthedocs.io.

.. _`WebVTT`: https://www.w3.org/TR/webvtt1/
.. _`HLS videos`: https://datatracker.ietf.org/doc/html/draft-pantos-hls-rfc8216bis

Installation
------------

::

    $ pip install webvtt-py

Usage
-----

.. code-block:: python

  import webvtt

  for caption in webvtt.read('captions.vtt'):
      print(caption.identifier)  # cue identifier if any
      print(caption.start)       # cue start time
      print(caption.end)         # cue end time
      print(caption.text)        # cue payload
      print(caption.voice)       # cue voice span if any
      print(caption.voices)      # voices of every voice span in the text

Writing captions
----------------

.. code-block:: python

  from webvtt import WebVTT, Caption

  vtt = WebVTT()

  vtt.captions.append(
      Caption('00:00:00.500', '00:00:07.000', 'Caption line 1\nCaption line 2')
  )
  vtt.captions.append(
      Caption('00:00:07.000', '00:00:11.890', ['Caption line 1', 'Caption line 2'])
  )

  vtt.save('captions.vtt')

  # or get the content without writing a file
  print(vtt.content)

Segmenting for HLS
------------------

.. code-block:: python

  import webvtt

  webvtt.segment('captions.vtt', 'output/path')

Converting captions from other formats
--------------------------------------

Supported formats:

* SubRip (.srt)
* YouTube SBV (.sbv)

.. code-block:: python

  import webvtt

  # write captions.vtt next to captions.srt
  vtt = webvtt.from_srt('captions.srt')
  vtt.save()

  # alternatively in a single line
  webvtt.from_sbv('captions.sbv').save()

  # write captions.srt and captions.sbv next to captions.vtt
  vtt = webvtt.read('captions.vtt')
  vtt.save_as_srt()
  vtt.save_as_sbv()

CLI
---
Caption segmentation, shifting, synchronizing, validation and conversion are
also available from the command line with the ``webvtt`` executable, for
WebVTT, SRT and SBV files. Given ``captions.vtt``:

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

The playlist ``out/prog_index.m3u8`` lists the segments:

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

A caption crossing a segment boundary is included in every segment it
overlaps, ``out/fileSequence1.webvtt``:

.. code-block:: text

  WEBVTT
  X-TIMESTAMP-MAP=MPEGTS:900000,LOCAL:00:00:00.000

  00:00:06.000 --> 00:00:12.000
  This caption spans two segments.

  00:00:14.500 --> 00:00:18.000
  Thanks for watching!

Use ``-d`` to change the segment duration and ``-m`` to change the MPEG-TS
value.

Show the captions 1.5 seconds earlier, writing them to a new file:

::

    $ webvtt shift captions.vtt -1.5 --output shifted.vtt

Without ``--output`` the shifted captions are written to standard output.
Use ``--start`` to only shift the captions starting at or after a time, as a
timestamp or a number of seconds, and ``--drop-before-zero`` to remove the
captions moved before the start.

Fix captions that drift out of sync by moving two or more points, here the
caption at 00:14.500 to 00:15.850 keeping the first one in place, or by
changing the frame rate they are timed for:

::

    $ webvtt sync captions.vtt -p 00:01.000 00:01.000 -p 00:14.500 00:15.850
    $ webvtt sync captions.vtt --fps 25 23.976 -o captions.vtt

Check the captions for problems, such as captions out of order, which are
printed one per line, with exit status 1 when there are errors:

::

    $ webvtt validate captions.vtt

Convert captions to another format, here by the extension of the output, or
with ``--to``:

::

    $ webvtt convert captions.srt -o captions.vtt
    $ webvtt convert captions.vtt --to srt --keep-formatting

The commands read SRT and SBV files by their extension, or with
``--format``, and ``--encoding`` reads a file in another encoding, as in
``webvtt shift captions.srt 2 --encoding cp1252 -o captions.srt``.

For all the options, run ``webvtt segment --help``, ``webvtt shift --help``,
``webvtt sync --help``, ``webvtt validate --help``, ``webvtt convert --help``
or ``man webvtt``, or see the `CLI documentation`_.

.. _`CLI documentation`: https://webvtt-py.readthedocs.io/en/latest/cli.html

License
-------

Licensed under the MIT License.

.. |pypi| image:: https://img.shields.io/pypi/v/webvtt-py.svg
    :target: https://pypi.org/project/webvtt-py/

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/webvtt-py.svg
    :alt: Supported Python versions
    :target: https://pypi.org/project/webvtt-py/

.. |license| image:: https://img.shields.io/pypi/l/webvtt-py.svg
    :alt: MIT License
    :target: https://opensource.org/licenses/MIT

.. |coverage| image:: https://codecov.io/gh/glut23/webvtt-py/graph/badge.svg?branch=master
    :target: https://codecov.io/gh/glut23/webvtt-py

.. |build-status| image:: https://github.com/glut23/webvtt-py/actions/workflows/ci.yml/badge.svg?branch=master
    :target: https://github.com/glut23/webvtt-py/actions/workflows/ci.yml

.. |docs-status| image:: https://readthedocs.org/projects/webvtt-py/badge/?version=latest
    :target: https://webvtt-py.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. |downloads| image:: https://static.pepy.tech/badge/webvtt-py
    :target: https://pepy.tech/project/webvtt-py
    :alt: Downloads