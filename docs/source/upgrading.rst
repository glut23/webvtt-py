Upgrading
=========

Upgrading to 0.7.0
------------------

0.7.0 has changes that may need updates to the code using the library. These
are the ones most likely to need them, with what to change. The
:doc:`history` lists all of them.


Python 3.10 or later
~~~~~~~~~~~~~~~~~~~~

Python 3.7, 3.8 and 3.9 are no longer supported, as they are end-of-life.
Stay on webvtt-py 0.6.0 to run on them:

::

    $ pip install 'webvtt-py<0.7'


Segmenting into a folder with an earlier run
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Segmenting into a folder that has the playlist or segments of an earlier run
raises ``FileExistsError``, and the ``segment`` command exits with an error,
instead of writing over them. Pass ``overwrite=True``, or ``--overwrite`` on
the command line, to replace them, which also deletes the segments of the
earlier run that the new playlist does not have:

.. code-block:: python

    import webvtt

    webvtt.segment('captions.vtt', 'output/path', overwrite=True)

::

    $ webvtt segment captions.vtt -o output/path --overwrite


Reading strings and bytes
~~~~~~~~~~~~~~~~~~~~~~~~~

``from_buffer`` raises ``TypeError`` for a string or bytes, which are not
file-like objects and it never read, instead of ``MalformedFileError``. Code
that catches ``MalformedFileError`` for them gets the new error. Read a string
with ``from_string``, and bytes as a file-like object:

.. code-block:: python

    import io

    import webvtt

    vtt = webvtt.from_string('WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHi\n')
    vtt = webvtt.from_buffer(io.BytesIO(b'WEBVTT\n'))

``from_buffer`` also raises ``ValueError`` for ``strict=True`` with the
``srt`` or ``sbv`` format, which have no strict parsing, instead of ignoring
it. Remove ``strict=True`` for those formats.


Saving to paths with an extension
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``save``, ``save_as_srt`` and the ``-o`` option of the CLI write a path with
an extension as given, so ``captions.webvtt`` is no longer saved as
``captions.webvtt.vtt``. Saving without a path, or to a folder, keeps the
extension of the file that was read when it is of the format, so captions
read from ``captions.webvtt`` are saved to it instead of ``captions.vtt``.
Pass the full path to save to another name:

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.webvtt')
    vtt.save()                 # captions.webvtt
    vtt.save('captions.vtt')   # captions.vtt


SRT encoding
~~~~~~~~~~~~

``save_as_srt`` saves captions read from SRT with an ``encoding`` in that
encoding, instead of UTF-8. Other captions are saved in UTF-8, instead of the
encoding of the locale. Pass the encoding to save in another one:

.. code-block:: python

    import webvtt

    vtt = webvtt.from_srt('captions.srt', encoding='cp1252')
    vtt.save_as_srt('cp1252.srt')                    # cp1252
    vtt.save_as_srt('utf-8.srt', encoding='utf-8')   # UTF-8


Byte Order Mark
~~~~~~~~~~~~~~~

``save`` raises ``ValueError`` for ``add_bom=True`` with an encoding without a
Byte Order Mark, such as ``latin-1``, and for ``add_bom=False`` with
``utf-8-sig``, ``utf-16`` or ``utf-32``, which always write one, instead of
ignoring ``add_bom``. Use an encoding that matches: ``utf-8`` without a Byte
Order Mark, or ``utf-8`` with ``add_bom=True`` for one. For UTF-16 or UTF-32
without a Byte Order Mark, use an encoding with the byte order, such as
``utf-16-le``.


Strict parsing
~~~~~~~~~~~~~~

Strict parsing raises errors for more content that is not valid WebVTT: cues
whose end time is not after the start time, blocks that are not a cue,
comment, style or region, comments where ``NOTE`` is not followed by a space,
a tab or a line break, styles after the first cue, and ``WEBVTT`` followed by
other text in the first line, such as ``WEBVTTX``. Files that passed strict
parsing before may raise an error now; read them without ``strict=True`` to
skip those blocks, as the default parsing does.

Default parsing also follows WebVTT more closely: styles after the first cue
and blocks such as ``NOTEBOOK`` are ignored, and SRT cues without an index are
read instead of skipped.


Text that cannot be written
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Writing WebVTT raises ``ValueError`` for ``-->`` in a comment or in the header
text, which WebVTT does not allow, instead of writing a file that cannot be
read back.


Caption text
~~~~~~~~~~~~

Setting ``Caption.text`` to a value that is not a string or a sequence of
lines raises ``TypeError`` instead of ``AttributeError``, and creating a
``Caption`` with lines that are not strings raises it instead of accepting
them. Code that catches ``AttributeError`` for it gets the new error.


Lists of items and lines
~~~~~~~~~~~~~~~~~~~~~~~~

``WebVTT`` keeps the lists given as arguments as its attributes, also when they
are empty, so adding to an empty list after creating the instance shows in it.
``Style`` copies a list of lines, as ``Caption`` does. Pass a copy, such as
``list(captions)``, to keep a list apart from the instance.
