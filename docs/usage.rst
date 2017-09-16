Usage
=====

Reading WebVTT caption files
----------------------------

.. code-block:: python

    from webvtt import WebVTT

    webvtt = WebVTT().read('captions.vtt')

    # we can iterate over the captions
    for caption in webvtt:
        print(caption.start)  # start timestamp in text format
        print(caption.end)  # end timestamp in text format
        print(caption.text)  # caption text

    # you can also iterate over the lines of a particular caption
    for line in webvtt[0].lines:
        print(line)


Creating captions
-----------------

.. code-block:: python

    from webvtt import WebVTT, Caption

    webvtt = WebVTT()

    # creating a caption with a list of lines
    caption = Caption(
        '00:00:00.500',
        '00:00:07.000',
        ['Caption line 1', 'Caption line 2']
    )

    # adding a caption
    webvtt.captions.append(caption)

    # creating another caption with a text
    caption = Caption(
        '00:00:07.000',
        '00:00:11.890',
        'Caption line 1\nCaption line 2']
    )

    webvtt.captions.append(caption)

    # save the document
    webvtt.save('my_captions.vtt')

    # write to opened file
    with open('my_captions.vtt', 'w') as fd:
        webvtt.write(fd)


Manipulating captions
---------------------

.. code-block:: python

    from webvtt import WebVTT

    webvtt = WebVTT().read('captions.vtt')

    # update start timestamp
    webvtt[0].start = '00:00:01.250'

    # update end timestamp
    webvtt[0].end = '00:00:03.890'

    # update caption text
    webvtt[0].text = 'My caption text'

    # delete a caption
    del webvtt.captions[2]


Converting captions
-------------------

You can read captions from the following formats:

* SubRip (.srt)
* YouTube SBV (.sbv)

.. code-block:: python

    from webvtt import WebVTT

    # to read from a different format use the method from_ followed by
    # the extension.
    webvtt = WebVTT().from_sbv('captions.sbv')
    webvtt.save()

    # if we just want to convert the file we can do this in one line
    WebVTT().from_sbv('captions.sbv').save()
