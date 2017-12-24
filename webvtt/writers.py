
class WebVTTWriter(object):

    def write(self, captions, f):
        f.write('WEBVTT\n')
        for c in captions:
            if c.identifier:
                f.write('\n' + c.identifier)
            f.write('\n{} --> {}\n'.format(c.start, c.end))
            f.writelines(['{}\n'.format(l) for l in c.lines])


class SRTWriter(object):

    def write(self, captions, f):
        for line_number, caption in enumerate(captions, start=1):
            f.write('{}\n'.format(line_number))
            f.write('{} --> {}\n'.format(self._to_srt_timestamp(caption.start_in_seconds),
                                         self._to_srt_timestamp(caption.end_in_seconds)))
            f.writelines(['{}\n'.format(l) for l in caption.lines])
            f.write('\n')

    def _to_srt_timestamp(self, total_seconds):
        hours = int(total_seconds / 3600)
        minutes = int(total_seconds / 60 - hours * 60)
        seconds = int(total_seconds - hours * 3600 - minutes * 60)
        milliseconds = round((total_seconds - seconds - hours * 3600 - minutes * 60)*1000)

        return '{:02d}:{:02d}:{:02d},{:03d}'.format(hours, minutes, seconds, milliseconds)


class SBVWriter(object):
    pass
