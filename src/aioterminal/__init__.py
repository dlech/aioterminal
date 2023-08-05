import asyncio
import contextlib
import errno
import functools
import os
import sys
import threading
import typing

# common doc strings and annotations


def char_mode(fd: int = ...) -> typing.ContextManager:
    """
    Context manager for setting terminal to "character" mode.

    This disables echo and allows reading one byte at a time without waiting for
    newline while retaining Ctrl-c functionality.

    This is also known as "cbreak" mode on *nix platforms.

    Args:
        fd: The file descriptor of a terminal. Default uses stdin.

    Raises:
        OSError: with ``errno.ENOTTY`` if *fd* is not a terminal

    Example::
        with char_mode():
            # read input in a loop
            ...
    """
    raise NotImplementedError


def read_chars(fd: int = ...) -> typing.AsyncGenerator[str, typing.Any]:
    """
    Async generator that returns each character from stdin as it becomes available.

    Since this is an async generator, if you break out of the for loop, you need
    to be sure to close the generator::

        async with contextlib.aclosing(read_chars()) as each_char:
            async for c in each_char:
                ...
                if ...:
                    break

    Args:
        fd: The file descriptor of a terminal. Default uses stdin.

    Raises:
        OSError: with ``errno.ENOTTY`` if *fd* is not a terminal
    """
    raise NotImplementedError


# common internals


def _assert_is_a_tty(fd) -> int:
    if fd is None:
        fd = sys.stdin.fileno()
    elif not isinstance(fd, int):
        fd = fd.fileno()

    # REVISIT: This might not work for all cases on windows
    if not os.isatty(fd):
        raise OSError(errno.ENOTTY, "fd is not a terminal")

    return fd


# platform-specific implementations


_ON_POSIX = "posix" in sys.builtin_module_names


if _ON_POSIX:
    import termios
    import tty

    @functools.wraps(char_mode)
    @contextlib.contextmanager
    def char_mode(fd=None):
        fd = _assert_is_a_tty(fd)

        old_attr = termios.tcgetattr(fd)
        tty.setcbreak(fd)

        try:
            yield
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, old_attr)

    @functools.wraps(read_chars)
    async def read_chars(fd=None):
        fd = _assert_is_a_tty(fd)

        with contextlib.ExitStack() as stack:
            loop = asyncio.get_running_loop()
            queue = asyncio.Queue[str]()

            # dup fd to get unique fd for add/remove reader
            f = stack.enter_context(os.fdopen(os.dup(fd)))

            def on_notify():
                # Have to use read1 to avoid blocking.
                # NB: setting stdin to O_NONBLOCK also sets stdout which
                # which breaks things like print()
                x = f.buffer.read1()
                queue.put_nowait(x.decode(f.encoding))

            loop.add_reader(f, on_notify)
            stack.callback(loop.remove_reader, f)

            while True:
                # REVISIT: how to handle EOF?
                for c in await queue.get():
                    yield c

else:
    import ctypes
    import msvcrt
    from ctypes import wintypes

    # https://learn.microsoft.com/en-us/windows/console/setconsolemode
    _ENABLE_PROCESSED_INPUT = 0x0001
    _ENABLE_LINE_INPUT = 0x0002
    _ENABLE_ECHO_INPUT = 0x0004
    _ENABLE_WINDOW_INPUT = 0x0008
    _ENABLE_MOUSE_INPUT = 0x0010
    _ENABLE_INSERT_MODE = 0x0020
    _ENABLE_QUICK_EDIT_MODE = 0x0040
    _ENABLE_VIRTUAL_TERMINAL_INPUT = 0x0200

    # https://learn.microsoft.com/en-us/windows/win32/procthread/thread-security-and-access-rights
    _THREAD_TERMINATE = 0x0001

    _SetConsoleMode = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HANDLE, wintypes.DWORD
    )(
        ("SetConsoleMode", ctypes.windll.kernel32),
        ((1, "hConsoleHandle"), (1, "dwMode")),
    )

    def errcheck(r, f, a):
        if not r:
            raise ctypes.WinError()

    _SetConsoleMode.errcheck = errcheck

    _GetConsoleMode = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HANDLE, wintypes.LPDWORD
    )(
        ("GetConsoleMode", ctypes.windll.kernel32),
        ((1, "hConsoleHandle"), (2, "lpMode")),
    )

    def errcheck(r, f, a):
        if not r:
            raise ctypes.WinError()

        return a[1].value

    _GetConsoleMode.errcheck = errcheck

    _FlushConsoleInputBuffer = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HANDLE)(
        ("FlushConsoleInputBuffer", ctypes.windll.kernel32),
        ((1, "hConsoleHandle"),),
    )

    def errcheck(r, f, a):
        if not r:
            raise ctypes.WinError()

    _FlushConsoleInputBuffer.errcheck = errcheck

    _ReadConsole = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HANDLE,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.LPDWORD,
        wintypes.LPVOID,
    )(
        ("ReadConsoleW", ctypes.windll.kernel32),
        (
            (1, "hConsoleHandle"),
            (1, "lpBuffer"),
            (1, "nNumberOfCharsToRead"),
            (2, "lpNumberOfCharsRead"),
            (5, "pInputControl"),
        ),
    )

    def errcheck(r, f, a):
        if not r:
            raise ctypes.WinError()

        return a[1][: a[3].value]

    _ReadConsole.errcheck = errcheck

    _CancelSynchronousIo = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HANDLE)(
        ("CancelSynchronousIo", ctypes.windll.kernel32), ((1, "hThread"),)
    )

    def errcheck(r, f, a):
        if not r:
            raise ctypes.WinError()

    _CancelSynchronousIo.errcheck = errcheck

    _OpenThread = ctypes.WINFUNCTYPE(
        wintypes.HANDLE, wintypes.DWORD, wintypes.BOOL, wintypes.DWORD
    )(
        ("OpenThread", ctypes.windll.kernel32),
        ((1, "dwDesiredAccess"), (1, "bInheritHandle"), (1, "dwThreadId")),
    )

    def errcheck(r, f, a):
        if not r:
            raise ctypes.WinError()

        return r

    _OpenThread.errcheck = errcheck

    _CloseHandle = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HANDLE)(
        ("CloseHandle", ctypes.windll.kernel32), ((1, "hObject"),)
    )

    def errcheck(r, f, a):
        if not r:
            raise ctypes.WinError()

    _CloseHandle.errcheck = errcheck

    del errcheck

    @functools.wraps(char_mode)
    @contextlib.contextmanager
    def char_mode(fd=None):
        fd = _assert_is_a_tty(fd)

        handle = msvcrt.get_osfhandle(fd)

        # NB: old_mode may not be valid (windows bug) which can cause later
        # call to SetConsoleMode to fail. Workaround is to set a valid mode
        # or get a new terminal before calling the char_mode() method.
        old_mode = _GetConsoleMode(handle)

        # roughly equivelent of posix cbreak mode
        _SetConsoleMode(
            handle, _ENABLE_PROCESSED_INPUT | _ENABLE_VIRTUAL_TERMINAL_INPUT
        )

        try:
            yield
        finally:
            _SetConsoleMode(handle, old_mode)

    @functools.wraps(read_chars)
    async def read_chars(fd=None):
        fd = _assert_is_a_tty(fd)

        with contextlib.ExitStack() as stack:
            handle = msvcrt.get_osfhandle(fd)
            loop = asyncio.get_running_loop()
            queue = asyncio.Queue[str]()
            event = threading.Event()

            def read_thread():
                buf = (wintypes.WCHAR * 256)()

                while not event.is_set():
                    x = _ReadConsole(handle, buf, len(buf))
                    loop.call_soon_threadsafe(queue.put_nowait, x)

            t = threading.Thread(target=read_thread, daemon=True)
            t.start()

            t_handle = _OpenThread(_THREAD_TERMINATE, False, t.native_id)
            stack.callback(_CloseHandle, t_handle)

            def abort():
                if t.is_alive():
                    event.set()
                    _CancelSynchronousIo(t_handle)

            stack.callback(abort)

            while True:
                # REVISIT: how to handle EOF?
                for c in await queue.get():
                    yield c
