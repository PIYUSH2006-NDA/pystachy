"""The io module's in-memory streams, StringIO and BytesIO, written for Pystachy.

CPython's io is a C module (Modules/_io); this one has StringIO, after Modules/_io/stringio.c of
CPython 3.13.16: the same reads, writes, seeks, newline translation and errors, on a str buffer
(lib/README.md). Positions and sizes count a str's bytes past ASCII, as len() and slicing do.
BytesIO follows Modules/_io/bytesio.c in the same way, on a bytes buffer.
"""

from typing import Self

__all__ = ["StringIO", "BytesIO", "SEEK_SET", "SEEK_CUR", "SEEK_END"]

SEEK_SET = 0
SEEK_CUR = 1
SEEK_END = 2
# the largest Py_ssize_t (PY_SSIZE_T_MAX), which bounds BytesIO's positions and size
_SSIZE_MAX = 9223372036854775807


class StringIO:
    """Text I/O implementation using an in-memory buffer.

    The initial_value argument sets the value of object.  The newline
    argument is like the one of TextIOWrapper's constructor.
    """

    def __init__(self, initial_value: str | None = "", newline: str | None = "\n") -> None:
        if newline is not None and newline != "" and newline != "\n" and newline != "\r" and newline != "\r\n":
            raise ValueError(f"illegal newline value: {newline!r}")
        # newline None: \r\n and \r are written as \n; "": nothing is translated, and \n, \r and
        # \r\n end lines; "\r" or "\r\n": each \n written is written as it; "\n": nothing at all
        self._newline = newline
        self._buf = ""  # the text, but for _tail
        self._tail: list[str] = []  # what was written at the end since _buf was last joined
        self._size = 0  # the length of the text: of _buf and _tail
        self._pos = 0
        self.closed = False
        self.line_buffering = False
        self.encoding: str | None = None
        self.errors: str | None = None
        if initial_value is not None and initial_value != "":
            self.write(initial_value)
            self._pos = 0

    def _check(self) -> None:
        if self.closed:
            raise ValueError("I/O operation on closed file")

    def _check_base(self) -> None:
        # (the methods StringIO has from IOBase say it with a full stop)
        if self.closed:
            raise ValueError("I/O operation on closed file.")

    def _join(self) -> None:
        if self._tail:
            self._buf = self._buf + "".join(self._tail)
            self._tail = []

    def getvalue(self) -> str:
        """Retrieve the entire contents of the object."""
        self._check()
        self._join()
        return self._buf

    def write(self, s: str) -> int:
        """Write string to file.

        Returns the number of characters written, which is always equal to
        the length of the string.
        """
        self._check()
        n = len(s)
        if self._newline is None:
            s = s.replace("\r\n", "\n").replace("\r", "\n")
        elif self._newline == "\r" or self._newline == "\r\n":
            s = s.replace("\n", self._newline)
        if s == "":
            return n
        if self._pos == self._size:
            self._tail.append(s)
        else:
            self._join()
            if self._pos > self._size:
                # a write past the end pads the gap with NULs
                self._buf = self._buf + "\0" * (self._pos - self._size)
                self._size = self._pos
            self._buf = self._buf[:self._pos] + s + self._buf[self._pos + len(s):]
        self._pos += len(s)
        if self._pos > self._size:
            self._size = self._pos
        return n

    def writelines(self, lines: list[str]) -> None:
        """Write a list of lines to stream."""
        self._check_base()
        for line in lines:
            self.write(line)

    def read(self, size: int | None = -1) -> str:
        """Read at most size characters, returned as a string.

        If the argument is negative or omitted, read until EOF
        is reached. Return an empty string at EOF.
        """
        self._check()
        self._join()
        n = self._size - self._pos
        if size is not None and 0 <= size < n:
            n = size
        if n <= 0:
            return ""
        start = self._pos
        self._pos += n
        return self._buf[start:self._pos]

    def readline(self, size: int | None = -1) -> str:
        """Read until newline or EOF.

        Returns an empty string if EOF is hit immediately.
        """
        self._check()
        self._join()
        start = self._pos
        if start >= self._size:
            return ""
        limit = self._size - start
        if size is not None and 0 <= size < limit:
            limit = size
        stop = start + limit
        buf = self._buf
        end = -1
        if self._newline is None or self._newline == "\n":
            i = buf.find("\n", start, stop)
            if i >= 0:
                end = i + 1
        elif self._newline == "":
            # the first \n, \r or \r\n (a \r at the limit ends the line)
            i = buf.find("\n", start, stop)
            j = buf.find("\r", start, i if i >= 0 else stop)
            if j >= 0:
                end = j + 2 if j + 1 < stop and buf[j + 1] == "\n" else j + 1
            elif i >= 0:
                end = i + 1
        else:
            i = buf.find(self._newline, start, stop)
            if i >= 0:
                end = i + len(self._newline)
        if end < 0:
            end = stop
        self._pos = end
        return buf[start:end]

    def readlines(self, hint: int | None = -1) -> list[str]:
        """Return a list of lines from the stream.

        hint can be specified to control the number of lines read: no more
        lines will be read if the total size (in bytes/characters) of all
        lines so far exceeds hint.
        """
        self._check_base()
        lines: list[str] = []
        total = 0
        while True:
            line = self.readline()
            if line == "":
                break
            lines.append(line)
            total += len(line)
            if hint is not None and 0 < hint < total:
                break
        return lines

    def __iter__(self) -> Self:
        self._check_base()
        return self

    def __enter__(self):  # (compiled only where a with statement calls it, as __exit__ is)
        """Context management protocol.  Returns self (an instance of IOBase)."""
        self._check_base()
        return self

    def __exit__(self, *args) -> None:
        """Context management protocol.  Calls close()"""
        self.close()

    def __next__(self) -> str:
        line = self.readline()
        if line == "":
            raise StopIteration
        return line

    def tell(self) -> int:
        """Tell the current file position."""
        self._check()
        return self._pos

    def seek(self, pos: int, whence: int = 0) -> int:
        """Change stream position.

        Seek to character offset pos relative to position indicated by whence:
            0  Start of stream (the default).  pos should be >= 0;
            1  Current position - pos must be 0;
            2  End of stream - pos must be 0.
        Returns the new absolute position.
        """
        self._check()
        if whence != 0 and whence != 1 and whence != 2:
            raise ValueError(f"Invalid whence ({whence}, should be 0, 1 or 2)")
        if pos < 0 and whence == 0:
            raise ValueError(f"Negative seek position {pos}")
        if whence != 0 and pos != 0:
            raise OSError("Can't do nonzero cur-relative seeks")
        if whence == 1:
            pos = self._pos
        elif whence == 2:
            pos = self._size
        self._pos = pos
        return pos

    def truncate(self, pos: int | None = None) -> int:
        """Truncate size to pos.

        The pos argument defaults to the current file position, as
        returned by tell().  The current file position is unchanged.
        Returns the new absolute position.
        """
        self._check()
        size = self._pos if pos is None else pos
        if size < 0:
            raise ValueError(f"Negative size value {size}")
        if size < self._size:
            self._join()
            self._buf = self._buf[:size]
            self._size = size
        return size

    def close(self) -> None:
        """Close the IO object.

        Attempting any further operation after the object is closed
        will raise a ValueError.

        This method has no effect if the file is already closed.
        """
        self.closed = True
        self._buf = ""
        self._tail = []

    def flush(self) -> None:
        """Does nothing: a StringIO has no buffer to write out."""

    def readable(self) -> bool:
        """Returns True if the IO object can be read."""
        self._check()
        return True

    def writable(self) -> bool:
        """Returns True if the IO object can be written."""
        self._check()
        return True

    def seekable(self) -> bool:
        """Returns True if the IO object can be seeked."""
        self._check()
        return True

    def isatty(self) -> bool:
        """Return whether this is an 'interactive' stream."""
        self._check_base()
        return False


class BytesIO:
    """Buffered I/O implementation using an in-memory bytes buffer."""

    def __init__(self, initial_bytes: bytes | None = None) -> None:
        # (CPython's default is no argument, as None is.) __init__ may be called again: with bytes,
        # the object holds them, open; without, it is emptied, and a closed one stays closed
        self._buf = b"" if initial_bytes is None else initial_bytes  # the bytes, but for _tail
        self._tail: list[bytes] = []  # what was written at the end since _buf was last joined
        self._size = len(self._buf)  # the length of the bytes: of _buf and _tail
        self._pos = 0
        if initial_bytes is not None or not hasattr(self, "_closed"):
            self._closed = False

    def _check(self) -> None:
        if self._closed:
            raise ValueError("I/O operation on closed file.")

    def _join(self) -> None:
        if self._tail:
            self._buf = self._buf + b"".join(self._tail)
            self._tail = []

    def _line(self, size: int) -> bytes:
        # the next line, of at most size bytes if size >= 0 (scan_eol, then read_bytes)
        start = self._pos
        n = self._size - start
        if 0 <= size < n:
            n = size
        if n <= 0:
            return b""
        self._join()
        i = self._buf.find(b"\n", start, start + n)
        if i >= 0:
            n = i + 1 - start
        self._pos = start + n
        return self._buf[start:self._pos]

    @property
    def closed(self) -> bool:
        """True if the file is closed."""
        return self._closed

    @closed.setter
    def closed(self, value: object) -> None:
        # (an attribute of the C type that has no setter)
        raise AttributeError("attribute 'closed' of '_io.BytesIO' objects is not writable")

    def readable(self) -> bool:
        """Returns True if the IO object can be read."""
        self._check()
        return True

    def writable(self) -> bool:
        """Returns True if the IO object can be written."""
        self._check()
        return True

    def seekable(self) -> bool:
        """Returns True if the IO object can be seeked."""
        self._check()
        return True

    def flush(self) -> None:
        """Does nothing."""
        self._check()

    def getvalue(self) -> bytes:
        """Retrieve the entire contents of the BytesIO object."""
        self._check()
        self._join()
        return self._buf

    def isatty(self) -> bool:
        """Always returns False.

        BytesIO objects are not connected to a TTY-like device."""
        self._check()
        return False

    def tell(self) -> int:
        """Current file position, an integer."""
        self._check()
        return self._pos

    def read(self, size: int | None = -1, /) -> bytes:
        """Read at most size bytes, returned as a bytes object.

        If the size argument is negative, read until EOF is reached.
        Return an empty bytes object at EOF."""
        self._check()
        n = self._size - self._pos
        if size is not None and 0 <= size < n:
            n = size
        if n <= 0:
            return b""
        self._join()
        start = self._pos
        self._pos += n
        return self._buf[start:self._pos]

    def read1(self, size: int | None = -1, /) -> bytes:
        """Read at most size bytes, returned as a bytes object.

        If the size argument is negative or omitted, read until EOF is
        reached.  Return an empty bytes object at EOF."""
        return self.read(size)

    def readline(self, size: int | None = -1, /) -> bytes:
        """Next line from the file, as a bytes object.

        Retain newline.  A non-negative size argument limits the maximum
        number of bytes to return (an incomplete line may be returned then).
        Return an empty bytes object at EOF."""
        self._check()
        return self._line(-1 if size is None else size)

    def readlines(self, size: int | None = None, /) -> list[bytes]:
        """List of bytes objects, each a line from the file.

        Call readline() repeatedly and return a list of the lines so read.
        The optional size argument, if given, is an approximate bound on the
        total number of bytes in the lines returned."""
        self._check()
        maxsize = -1 if size is None else size
        lines: list[bytes] = []
        total = 0
        while True:
            line = self._line(-1)
            if line == b"":
                break
            lines.append(line)
            total += len(line)
            # (the C type's bound: the lines stop once their total reaches it)
            if maxsize > 0 and total >= maxsize:
                break
        return lines

    def truncate(self, size: int | None = None, /) -> int:
        """Truncate the file to at most size bytes.

        Size defaults to the current file position, as returned by tell().
        The current file position is unchanged.  Returns the new size."""
        self._check()
        n = self._pos if size is None else size
        if n < 0:
            raise ValueError(f"negative size value {n}")
        if n < self._size:
            self._join()
            self._buf = self._buf[:n]
            self._size = n
        return n

    def __iter__(self) -> Self:
        # (the C type's is the object itself, open or closed: its __next__ checks)
        return self

    def __next__(self) -> bytes:
        self._check()
        line = self._line(-1)
        if line == b"":
            raise StopIteration
        return line

    def seek(self, pos: int, whence: int = 0, /) -> int:
        """Change stream position.

        Seek to byte offset pos relative to position indicated by whence:
             0  Start of stream (the default).  pos should be >= 0;
             1  Current position - pos may be negative;
             2  End of stream - pos usually negative.
        Returns the new absolute position."""
        if whence < -2147483648 or whence > 2147483647:
            # (whence is a C int, converted before anything is checked)
            raise OverflowError("Python int too large to convert to C int")
        self._check()
        if pos < 0 and whence == 0:
            raise ValueError(f"negative seek value {pos}")
        if whence == 1:
            if pos > _SSIZE_MAX - self._pos:
                raise OverflowError("new position too large")
            pos += self._pos
        elif whence == 2:
            if pos > _SSIZE_MAX - self._size:
                raise OverflowError("new position too large")
            pos += self._size
        elif whence != 0:
            raise ValueError(f"invalid whence ({whence}, should be 0, 1 or 2)")
        if pos < 0:
            pos = 0
        self._pos = pos
        return pos

    def write(self, b: bytes, /) -> int:
        """Write bytes to file.

        Return the number of bytes written."""
        self._check()
        n = len(b)
        if n == 0:
            return 0
        if self._pos > _SSIZE_MAX - n:
            raise OverflowError("new buffer size too large")
        if self._pos == self._size:
            self._tail.append(b)
        else:
            self._join()
            if self._pos > self._size:
                # a write past the end pads the gap with NUL bytes
                self._buf = self._buf + b"\0" * (self._pos - self._size) + b
            else:
                self._buf = self._buf[:self._pos] + b + self._buf[self._pos + n:]
        self._pos += n
        if self._pos > self._size:
            self._size = self._pos
        return n

    def writelines(self, lines, /) -> None:  # (lines: any iterable of bytes)
        """Write lines to the file.

        Note that newlines are not added.  lines can be any iterable object
        producing bytes-like objects.  This is equivalent to calling write()
        for each element."""
        self._check()
        for line in lines:
            self.write(line)

    def close(self) -> None:
        """Disable all I/O operations."""
        self._closed = True
        self._buf = b""
        self._tail = []

    def __enter__(self):  # (compiled only where a with statement calls it, as __exit__ is)
        self._check()
        return self

    def __exit__(self, *args) -> None:
        self.close()
