"""Utils module."""

import locale
import os
import re
import typing
import codecs

CODEC_BOMS = {
    'utf-8': codecs.BOM_UTF8,
    'utf-32-le': codecs.BOM_UTF32_LE,
    'utf-32-be': codecs.BOM_UTF32_BE,
    'utf-16-le': codecs.BOM_UTF16_LE,
    'utf-16-be': codecs.BOM_UTF16_BE
}

# the line terminators of WebVTT, characters like U+2028 do not break lines
_LINE_TERMINATOR = re.compile(r'\r\n|\r|\n')


def _split_lines(text: str) -> typing.List[str]:
    """
    Split text into lines on CR, LF and CRLF.

    Works like ``str.splitlines`` but only breaks lines on the WebVTT line
    terminators, other characters like U+2028 or form feed stay in the line.

    :param text: the text to split
    :returns: the list of lines, without a final empty line when the text
        ends with a line terminator
    """
    lines = _LINE_TERMINATOR.split(text)
    if not lines[-1]:
        lines.pop()
    return lines


class FileWrapper:
    """File handling functionality with built-in support for Byte OrderMark."""

    def __init__(
            self,
            file_path: str,
            mode: typing.Optional[str] = None,
            encoding: typing.Optional[str] = None
            ):
        """
        Initialize.

        :param file_path: path to the file
        :param mode: mode in which the file is opened
        :param encoding: name of the encoding used to decode the file
        """
        self.file_path = file_path
        self.mode = mode or 'r'
        self.bom_encoding = self.detect_bom_encoding(file_path)
        self.encoding = (self.bom_encoding or
                         encoding or
                         'utf-8'
                         )

    @classmethod
    def open(
            cls,
            file_path: str,
            mode: typing.Optional[str] = None,
            encoding: typing.Optional[str] = None
            ) -> 'FileWrapper':
        """
        Open a file.

        :param file_path: path to the file
        :param mode: mode in which the file is opened
        :param encoding: name of the encoding used to decode the file
        """
        return cls(file_path, mode, encoding)

    def __enter__(self):
        """Enter context."""
        self.file = open(
            file=self.file_path,
            mode=self.mode,
            encoding=self.encoding
            )
        if self.bom_encoding:
            self.file.seek(len(CODEC_BOMS[self.bom_encoding]))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        self.file.close()

    @staticmethod
    def detect_bom_encoding(file_path: str) -> typing.Optional[str]:
        """
        Detect the encoding of a file based on the presence of the BOM.

        :param file_path: path to the file
        :returns: the encoding if BOM is found or None.
        """
        with open(file_path, mode='rb') as f:
            first_bytes = f.read(4)
            for encoding, bom in CODEC_BOMS.items():
                if first_bytes.startswith(bom):
                    return encoding
        return None


def _write_text_file(
        file_path: str,
        text: str,
        encoding: typing.Optional[str] = None
        ):
    """
    Write text to a file, encoding all of it before the file is opened.

    An error while encoding, such as a character the encoding cannot write
    or an unknown encoding, is raised before the file is opened, so an
    existing file is left unchanged. Line feeds are written as the line
    separator of the platform, as in a file opened in text mode.

    :param file_path: path to the file
    :param text: the text to write
    :param encoding: name of the encoding used to encode the text, the
        preferred encoding of the locale if None, as in a file opened in
        text mode
    """
    if encoding is None:
        encoding = locale.getpreferredencoding(False)

    data = text.replace('\n', os.linesep).encode(encoding)
    with open(file_path, 'wb') as f:
        f.write(data)


def iter_blocks_of_lines(
        lines: typing.Iterable[str]
        ) -> typing.Generator[typing.List[str], None, None]:
    """
    Iterate blocks of text.

    :param lines: lines of text.
    """
    current_text_block = []

    for line in lines:
        if line.strip():
            current_text_block.append(line)
        elif current_text_block:
            yield current_text_block
            current_text_block = []

    if current_text_block:
        yield current_text_block
