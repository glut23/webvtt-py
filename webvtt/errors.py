"""Errors module."""


class MalformedFileError(Exception):
    """
    File is not in the right format.

    Raised when reading captions whose content is not valid for the
    expected format (WebVTT, SRT or SBV), e.g. a WebVTT file missing the
    ``WEBVTT`` header.
    """


class MalformedCaptionError(Exception):
    """
    Caption not in the right format.

    Raised when a timestamp is not valid, e.g. when creating a
    :class:`~webvtt.models.Caption`, setting its ``start`` or ``end`` or
    reading a file that contains a cue with an invalid timestamp. Also
    raised when a cue setting is not valid, e.g. when setting one of
    :class:`~webvtt.models.CueSettings`.
    """


class MissingFilenameError(Exception):
    """
    Missing a filename when saving to disk.

    Raised when saving captions without an output path and the
    :class:`~webvtt.webvtt.WebVTT` instance was not read from a file.
    """
