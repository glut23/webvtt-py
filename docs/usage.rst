Usage
=====

Reading WebVTT caption files
----------------------------

.. code-block:: python

    import webvtt

    # we can iterate over the captions
    for caption in webvtt.read('captions.vtt'):
        print(caption.start)  # start timestamp in text format
        print(caption.end)  # end timestamp in text format
        print(caption.text)  # caption text

    # you can also iterate over the lines of a particular caption
    for line in vtt[0].lines:
        print(line)

    # caption text is returned clean without class tags
    # we can access the raw text of a caption with raw_text
    >>> vtt[0].text
    'This is a caption text'
    >>> vtt[0].raw_text
    'This is a <c.colorE5E5E5>caption</c> text'

    # caption identifiers
    >>> vtt[0].identifier
    'crédit de transcription'


Reading WebVTT caption files from file-like object
--------------------------------------------------

.. code-block:: python

    import webvtt
    import requests
    from io import StringIO

    payload = requests.get('http://subtitles.com/1234.vtt').text()
    buffer = StringIO(payload)

    for caption in webvtt.read_buffer(buffer):
        print(caption.start)
        print(caption.end)
        print(caption.text)


Creating captions
-----------------

.. code-block:: python

    from webvtt import WebVTT, Caption

    vtt = WebVTT()

    # creating a caption with a list of lines
    caption = Caption(
        '00:00:00.500',
        '00:00:07.000',
        ['Caption line 1', 'Caption line 2']
    )

    # adding a caption
    vtt.captions.append(caption)

    # creating another caption with a text
    caption = Caption(
        '00:00:07.000',
        '00:00:11.890',
        'Caption line 1\nCaption line 2'
    )

    vtt.captions.append(caption)


Manipulating captions
---------------------

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    # update start timestamp
    vtt[0].start = '00:00:01.250'

    # update end timestamp
    vtt[0].end = '00:00:03.890'

    # update caption text
    vtt[0].text = 'My caption text'

    # delete a caption
    del vtt.captions[2]


Saving captions
---------------

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    # save to original file
    vtt.save()

    # save to a different file
    vtt.save('my_captions.vtt')

    # write to opened file
    with open('my_captions.vtt', 'w') as fd:
        vtt.write(fd)


Fetching WebVTT formatted Captions
------------------------------------

WebVTT formatted captions content can be obtained without having to create an output file.

.. code-block:: python

    import webvtt

    vtt = webvtt.read('captions.vtt')

    # Print the captions formatted in webvtt
    print(vtt.content)


Converting captions
-------------------

You can read captions from the following formats:

* SubRip (.srt)
* YouTube SBV (.sbv)

.. code-block:: python

    import webvtt

    # to read from a different format use the method from_ followed by
    # the extension.
    vtt = webvtt.from_sbv('captions.sbv')
    vtt.save()

    # if we just want to convert the file we can do this in one line
    webvtt.from_sbv('captions.sbv').save()

Also we can convert WebVTT to other formats:

* SubRip (.srt)

.. code-block:: python

    import webvtt

    # save in SRT format
    vtt = webvtt.read('captions.vtt')
    vtt.save_as_srt()

    # write to opened file in SRT format
    with open('my_captions.srt', 'w') as fd:
        vtt.write(fd, format='srt')
