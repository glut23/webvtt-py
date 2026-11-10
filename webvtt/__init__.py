"""Main webvtt package."""

__version__ = '0.8.0'

from .webvtt import WebVTT
from . import segmenter
from .models import (  # noqa
    Caption, CueSettings, ParseIssue, Region, Style, ValidationIssue
    )

__all__ = [
    'WebVTT', 'Caption', 'CueSettings', 'ParseIssue', 'Region', 'Style',
    'ValidationIssue'
    ]

read = WebVTT.read
from_buffer = WebVTT.from_buffer
from_srt = WebVTT.from_srt
from_sbv = WebVTT.from_sbv
from_string = WebVTT.from_string
segment = segmenter.segment
