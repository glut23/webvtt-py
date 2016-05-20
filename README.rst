webvtt-py
=========

.. image:: https://travis-ci.org/glut23/webvtt-py.svg?branch=master
    :target: https://travis-ci.org/glut23/webvtt-py

``webvtt-py`` is a Python module for reading/writing WebVTT_ caption files. It also features caption segmentation useful when captioning `HLS videos`_.

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

License
-------

Licensed under the MIT License.