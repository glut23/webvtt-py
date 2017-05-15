from math import ceil, floor
from .generic import Caption
from webvtt.main import WebVTT

MPEGTS = 0
SECONDS = 200  # default number of seconds per segment


class WebVTTSegmenter(object):
    """
    Provides segmentation of WebVTT captions for HTTP Live Streaming (HLS).
    """
    def __init__(self):
        self._total_segments = 0
        self._output_writer = ''
        self._seconds = 0
        self._mpegts = 0
        self._segments = []

    def _validate_webvtt(self, webvtt):
        # Validates that the captions is a list and all the captions are instances of Caption.
        if not isinstance(webvtt, WebVTT):
            return False
        for c in webvtt.captions:
            if not isinstance(c, Caption):
                return False
        return True

    def _slice_segments(self, captions):
        self._segments = [[] for _ in range(self.total_segments)]

        for c in captions:
            segment_index_start = int(floor(float(c.start_in_seconds) / float(self.seconds)))
            self.segments[segment_index_start].append(c)

            # Also include a caption in other segments based on the end time.
            segment_index_end = int(floor(float(c.end_in_seconds) / float(self.seconds)))
            if segment_index_end > segment_index_start:
                for i in range(segment_index_start + 1, segment_index_end + 1):
                    self.segments[i].append(c)

    def _write_segments(self):
        for index in range(self.total_segments):
            with self._output_writer.open('fileSequence{}.webvtt'.format(index)) as f:
                f.write('WEBVTT\n')
                f.write('X-TIMESTAMP-MAP=MPEGTS:{},LOCAL:00:00.000\n'.format(self._mpegts))

                for caption in self.segments[index]:
                    f.write('\n{} --> {}\n'.format(caption.start, caption.end))
                    f.writelines(caption.lines)#['{}\n'.format(l) for l in caption.lines])

    def _write_manifest(self, captions, target_seconds=SECONDS):
        with self._output_writer.open('prog_index.m3u8') as f:
            f.write('#EXTM3U\n')
            f.write('#EXT-X-TARGETDURATION:{}\n'.format(self.seconds))
            f.write('#EXT-X-VERSION:5\n')
            f.write('#EXT-X-PLAYLIST-TYPE:VOD\n')
            
            remaining_seconds = captions[-1].end_in_seconds
            print(remaining_seconds)
            
            for i in range(self.total_segments):
                segment_length = "{0:.3f}".format(min(target_seconds,remaining_seconds))
                f.write('#EXTINF:{0}\n'.format(segment_length))
                f.write('fileSequence{}.webvtt\n'.format(i))
                remaining_seconds-=target_seconds

            f.write('#EXT-X-ENDLIST\n')

    def segment(self, webvtt, output='', seconds=SECONDS, mpegts=MPEGTS):
        """Segments the captions based on a number of seconds."""
        captions = WebVTT().read(webvtt).captions

        self._total_segments = 0 if not captions else int(ceil(float(captions[-1].end_in_seconds) / float(seconds)))
        self._output_writer = output
        self._seconds = seconds
        self._mpegts = mpegts

        self._slice_segments(captions)
        self._write_segments()
        self._write_manifest(captions, seconds)

    @property
    def seconds(self):
        """Returns the number of seconds used for segmenting captions."""
        return self._seconds

    @property
    def total_segments(self):
        """Returns the total of segments."""
        return self._total_segments

    @property
    def segments(self):
        """Return the list of segments."""
        return self._segments
