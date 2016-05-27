webvtt-py
=========

.. image:: https://img.shields.io/pypi/v/webvtt-py.svg
        :target: https://pypi.python.org/pypi/webvtt-py

.. image:: https://travis-ci.org/glut23/webvtt-py.svg?branch=master
        :target: https://travis-ci.org/glut23/webvtt-py

.. image:: https://readthedocs.org/projects/webvtt-py/badge/?version=latest
        :target: http://webvtt-py.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

``webvtt-py`` is a Python module for reading/writing WebVTT_ caption files. It also features caption segmentation useful when captioning `HLS videos`_.

Requires Python 3.3+.

Documentation is available at http://webvtt-py.readthedocs.io.

.. _`WebVTT`: http://dev.w3.org/html5/webvtt/
.. _`HLS videos`: https://tools.ietf.org/html/draft-pantos-http-live-streaming-19

Installation
------------

::

    $ pip install webvtt-py

Usage
-----

.. code-block:: python

  from webvtt import WebVTT

  webvtt = WebVTT().read('captions.vtt')
  for c in webvtt.captions:
      print(c.start)
      print(c.end)
      print(c.text)

Segmenting for HLS
------------------

.. code-block:: python

  from webvtt import WebVTTSegmenter

  WebVTTSegmenter().segment('captions.vtt', 'output/path')

Converting SRT captions
-----------------------

.. code-block:: python

  from webvtt import WebVTT

  webvtt = WebVTT().from_srt('captions.srt')
  webvtt.save()


CLI
---
Caption segmentation is also available from the command line:
::

    $ webvtt segment captions.vtt --output destination/directoy

License
-------

Licensed under the MIT License.