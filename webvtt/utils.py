"""Utils module."""

import locale
import os
import re
import codecs
from collections.abc import Generator, Iterable

CODEC_BOMS = {
    'utf-8': codecs.BOM_UTF8,
    'utf-32-le': codecs.BOM_UTF32_LE,
    'utf-32-be': codecs.BOM_UTF32_BE,
    'utf-16-le': codecs.BOM_UTF16_LE,
    'utf-16-be': codecs.BOM_UTF16_BE
}

# the codecs that always write a Byte Order Mark
_BOM_WRITING_CODECS = ('utf-8-sig', 'utf-16', 'utf-32')

# the line terminators of WebVTT, characters like U+2028 do not break lines
_LINE_TERMINATOR = re.compile(r'\r\n|\r|\n')

# a path to a file or a folder, as a string or a path object such as
# pathlib.Path
_Path = str | os.PathLike[str]

# the line number where a block of text starts, from 1, and its lines
_NumberedBlock = tuple[int, list[str]]


def _split_lines(text: str) -> list[str]:
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


def _check_errors(errors: str | None) -> None:
    """
    Check the name of an error handler for decoding.

    Decoding only looks up the handler on invalid bytes, so a wrong name
    would otherwise go unnoticed until a file has them.

    :param errors: the name of the error handler, or None for the default
    :raises LookupError: if the error handler is not known
    """
    if errors is not None:
        codecs.lookup_error(errors)


class FileWrapper:
    """File handling functionality with built-in support for Byte OrderMark."""

    def __init__(
            self,
            file_path: _Path,
            mode: str | None = None,
            encoding: str | None = None,
            errors: str | None = None
            ):
        """
        Initialize.

        :param file_path: path to the file
        :param mode: mode in which the file is opened
        :param encoding: name of the encoding used to decode the file
        :param errors: how decoding errors are handled, as in open()

        :raises LookupError: if the error handler is not known
        """
        _check_errors(errors)
        self.file_path = file_path
        self.mode = mode or 'r'
        self.errors = errors
        self.bom_encoding = self.detect_bom_encoding(file_path)
        self.encoding = (self.bom_encoding or
                         encoding or
                         'utf-8'
                         )

    @classmethod
    def open(
            cls,
            file_path: _Path,
            mode: str | None = None,
            encoding: str | None = None,
            errors: str | None = None
            ) -> 'FileWrapper':
        """
        Open a file.

        :param file_path: path to the file
        :param mode: mode in which the file is opened
        :param encoding: name of the encoding used to decode the file
        :param errors: how decoding errors are handled, as in open()
        """
        return cls(file_path, mode, encoding, errors)

    def __enter__(self) -> 'FileWrapper':
        """Enter context."""
        self.file = open(
            file=self.file_path,
            mode=self.mode,
            encoding=self.encoding,
            errors=self.errors
            )
        if self.bom_encoding:
            self.file.seek(len(CODEC_BOMS[self.bom_encoding]))
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Exit context."""
        self.file.close()

    @staticmethod
    def detect_bom_encoding(file_path: _Path) -> str | None:
        """
        Detect the encoding of a file based on the presence of the BOM.

        :param file_path: path to the file
        :returns: the encoding if BOM is found or None.
        """
        with open(file_path, mode='rb') as f:
            return _bom_encoding(f.read(4))


def _bom_encoding(data: bytes) -> str | None:
    """
    Return the encoding of the BOM at the start of the data.

    :param data: the data, or its first bytes
    :returns: the encoding if BOM is found or None.
    """
    for encoding, bom in CODEC_BOMS.items():
        if data.startswith(bom):
            return encoding
    return None


def _write_text_file(
        file_path: _Path,
        text: str,
        encoding: str | None = None
        ) -> None:
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
        lines: Iterable[str]
        ) -> Generator[list[str], None, None]:
    """
    Iterate blocks of text.

    :param lines: lines of text.
    """
    for _, block in _iter_numbered_blocks(lines):
        yield block


def _iter_numbered_blocks(
        lines: Iterable[str]
        ) -> Generator[_NumberedBlock, None, None]:
    """
    Iterate blocks of text with the line number where each one starts.

    :param lines: lines of text.
    :returns: the line number where each block starts, from 1, and its lines
    """
    current_text_block: list[str] = []
    number = 0

    for number, line in enumerate(lines, 1):
        if line.strip():
            current_text_block.append(line)
        elif current_text_block:
            yield number - len(current_text_block), current_text_block
            current_text_block = []

    if current_text_block:
        yield number + 1 - len(current_text_block), current_text_block
