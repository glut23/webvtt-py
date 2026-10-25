import contextlib
import os
import tempfile


@contextlib.contextmanager
def named_temporary_file(*args, **kwargs):
    """
    Return a named temporary file that can be opened again by its name.

    On Windows, a file of tempfile.NamedTemporaryFile cannot be opened
    again while it is open, so it is created with delete=False and removed
    when the block ends.
    """
    f = tempfile.NamedTemporaryFile(*args, delete=False, **kwargs)
    try:
        with f:
            yield f
    finally:
        os.remove(f.name)
