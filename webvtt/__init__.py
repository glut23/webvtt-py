from .main import WebVTT
from .segmenter import WebVTTSegmenter
from .generic import Caption

__version__ = '0.4.1'

read = WebVTT.read
from_srt = WebVTT.from_srt
from_sbv = WebVTT.from_sbv
segment = WebVTTSegmenter().segment
