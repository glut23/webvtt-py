from .core import WebVTT
from .segmenter import WebVTTSegmenter
from .structures import Caption
from .exceptions import (
    MalformedFileError, MalformedCaptionError, InvalidCaptionsError,
    MissingFilenameError)

__all__ = (
    'WebVTT', 'WebVTTSegmenter', 'Caption', 'read', 'from_srt', 'from_sbv', 'segment',
    'MalformedFileError', 'MalformedCaptionError', 'InvalidCaptionsError', 'MissingFilenameError'
)

__version__ = '0.4.1'

read = WebVTT.read
from_srt = WebVTT.from_srt
from_sbv = WebVTT.from_sbv
segment = WebVTTSegmenter().segment
