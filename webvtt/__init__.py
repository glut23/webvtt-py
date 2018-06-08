__version__ = '0.4.2'

from .webvtt import *
from .segmenter import *
from .structures import *
from .errors import *

__all__ = webvtt.__all__ + segmenter.__all__ + structures.__all__ + errors.__all__

read = WebVTT.read
from_srt = WebVTT.from_srt
from_sbv = WebVTT.from_sbv
list_formats = WebVTT.list_formats
segment = WebVTTSegmenter().segment
