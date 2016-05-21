Usage
=====

Reading WebVTT caption files
----------------------------

.. code-block:: python

    from webvtt import WebVTT

    webvtt = WebVTT().read('captions.vtt')

    # we can iterate over the captions
    for caption in webvtt.captions:
        print(caption.start)  # start timestamp in text format
        print(caption.end)  # end timestamp in text format
        print(caption.text)  # caption text

    # you can also iterate over the caption lines
    for line in webvtt.captions[0].lines:
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

    webvtt.captions.append(caption)

    # creating another caption but with a text
    caption = Caption(
        '00:00:07.000',
        '00:00:11.890',
        'Caption line 1\nCaption line 2']
    )

    webvtt.captions.append(caption)

    # save the document
    webvtt.save('my_captions.vtt')


Manipulating captions
---------------------

.. code-block:: python

    from webvtt import WebVTT

    webvtt = WebVTT().read('captions.vtt')

    # update start timestamp
    webvtt.captions[0].start = '00:00:01.250'

    # update end timestamp
    webvtt.captions[1].end = '00:00:12.890'

    # update caption text
    webvtt.captions[2].text = 'Single line caption text'

