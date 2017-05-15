"""
Usage:
  webvtt segment <file> [--target-duration=SECONDS] [--mpegts=OFFSET] [--output=<dir>]
  webvtt -h | --help
  webvtt --version

Options:
  -h --help                  Show this screen.
  --version                  Show version.
  --target-duration=SECONDS  Target duration of each segment in seconds [default: 200].
  --mpegts=OFFSET            Presentation timestamp value [default: 0].
  --output=<dir>             Output to directory [default: ./].

Examples:
  webvtt segment captions.vtt --output destination/directory
"""

from docopt import docopt

from . import WebVTTSegmenter, __version__
from io import FileReader, FileWriter, S3ObjectWriter

def main():
    """Main entry point for CLI commands."""
    options = docopt(__doc__, version=__version__)
    if options['segment']:
        segment(
            options['<file>'],
            options['--output'],
            options['--target-duration'],
            options['--mpegts'],
        )


def segment(f, output, target_duration, mpegts):
    """Segment command."""
    try:
        target_duration = int(target_duration)
    except ValueError:
        exit('Error: Invalid target duration.')

    try:
        mpegts = int(mpegts)
    except ValueError:
        exit('Error: Invalid MPEGTS value.')

    source = FileReader(f)
    output = FileWriter(f)
    #output = S3ObjectWriter('bucket', 'keyprefix')
    WebVTTSegmenter().segment(source, output, target_duration, mpegts)
