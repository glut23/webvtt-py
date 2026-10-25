"""Main webvtt package."""

__version__ = '0.6.0'
__author__ = 'Alejandro Mendez'
__author_email__ = 'amendez23@gmail.com'

from .webvtt import WebVTT
from . import segmenter
from .models import Caption, CueSettings, Region, Style  # noqa

__all__ = ['WebVTT', 'Caption', 'CueSettings', 'Region', 'Style']

read = WebVTT.read
read_buffer = WebVTT.read_buffer
from_buffer = WebVTT.from_buffer
from_srt = WebVTT.from_srt
from_sbv = WebVTT.from_sbv
from_string = WebVTT.from_string
segment = segmenter.segment
