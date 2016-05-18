webvtt-py
=========

.. image:: https://travis-ci.org/glut23/webvtt-py.svg?branch=master
    :target: https://travis-ci.org/glut23/webvtt-py

``webvtt-py`` is a Python module for reading/writing WebVTT_ caption files. It also features caption segmentation useful when captioning `HLS videos`_.

.. _`WebVTT`: http://dev.w3.org/html5/webvtt/
.. _`HLS videos`: https://tools.ietf.org/html/draft-pantos-http-live-streaming-19

Usage
-----

.. code-block:: python
    from webvtt import WebVTT

    webvtt = WebVTT().read('captions.vtt')
    for c in webvtt.captions:
        print(c.start_as_timestamp)
        print(c.end_as_timestamp)
        print('\n'.join(c.lines))

Segmenting for HLS
------------------

.. code-block:: python
    from webvtt import WebVTT, WebVTTSegmenter

    webvtt = WebVTT().read('captions.vtt')
    WebVTTSegmenter().segment(webvtt.captions, 'output/path')

Converting SRT captions
-----------------------

.. code-block:: python
    from webvtt import WebVTT

    webvtt = WebVTT().from_srt('captions.srt')
    webvtt.save()