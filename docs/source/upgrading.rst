Upgrading
=========

Upgrading to 0.8.0
------------------

0.8.0 has changes that may need updates to the code using the library. These
are the ones most likely to need them, with what to change. The
:doc:`history` lists all of them.


Total length
~~~~~~~~~~~~

``total_length`` returns a float with the milliseconds, from the earliest
start to the latest end of the captions, instead of whole seconds from the
start of the first caption to the end of the last one, which was wrong for
captions out of order. Round it or convert it to an ``int`` where whole
seconds are needed:

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')
    vtt.total_length       # 3.5
    int(vtt.total_length)  # 3


Comparing styles and captions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``Style`` and ``WebVTT`` are equal when they have the same content, as
``Caption`` and ``Region`` are, instead of only to themselves. For the same
reason they can no longer be used in sets or as dictionary keys, which raises
``TypeError``. Compare them with ``is`` to tell whether they are the same
object, and key a dictionary by ``id()`` or keep them in a list:

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')
    other = webvtt.read('captions.vtt')
    vtt == other  # True, before False
    vtt is other  # False

    files = {id(vtt): 'captions.vtt'}


Byte Order Mark of SRT and SBV files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``from_srt`` and ``from_sbv`` keep the Byte Order Mark of the file, as
``read`` does, and ``save_as_srt`` keeps it and saves in the encoding of the
file that was read, as ``save`` does, instead of saving in UTF-8 without it.
Pass ``add_bom=False`` to save without it, and ``encoding`` to save in another
encoding:

.. code-block:: python

    import webvtt

    vtt = webvtt.from_srt('captions_with_bom.srt')
    vtt.save_as_srt('with_bom.srt')
    vtt.save_as_srt('without_bom.srt', add_bom=False)


SRT colours and positions
~~~~~~~~~~~~~~~~~~~~~~~~~

Reading SRT converts its markup to WebVTT. A ``font`` tag with a ``color``
becomes a ``c`` tag with a class named from the colour, with a ``STYLE`` block
that gives the class its colour, other ``font`` tags are removed, keeping
their text, and a ``{\anN}`` tag becomes the ``line`` and ``align`` cue
settings. ``raw_text`` has the ``c`` tags instead of the ``font`` tags, and
``text`` no longer has the ``{\anN}`` tags. Read the position from the cue
settings, and save with ``keep_formatting`` to write the ``font`` tags back:

.. code-block:: python

    import webvtt

    # 1
    # 00:00:01,000 --> 00:00:02,500
    # {\an8}<font color="#ff0000">Hello</font> world
    vtt = webvtt.from_srt('captions.srt')

    vtt[0].text           # 'Hello world', before '{\an8}Hello world'
    vtt[0].raw_text       # '<c.color-ff0000>Hello</c> world'
    vtt[0].settings.line  # '0', at the top

    vtt.save_as_srt('captions.srt', keep_formatting=True)


SRT and SBV files in the CLI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The commands of the CLI read files with the ``.srt`` and ``.sbv`` extensions
as SRT and SBV, instead of WebVTT. A WebVTT file with one of these extensions
needs ``--format vtt``:

::

    $ webvtt validate captions.srt --format vtt


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
