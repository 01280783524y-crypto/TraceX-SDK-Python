import asyncio
import sys
import threading
from types import TracebackType
from typing import Callable, Optional, Any

CaptureCallback = Callable[[Optional[type], Optional[BaseException], Optional[TracebackType]], None]


class ExceptionHooksManager:
    def __init__(self, on_exception: CaptureCallback) -> None:
        self._on_exception = on_exception
        self._installed = False
        self._original_sys_hook = sys.excepthook
        self._original_threading_hook = threading.excepthook

    def install(self) -> None:
        if self._installed:
            return

        self._original_sys_hook = sys.excepthook
        self._original_threading_hook = threading.excepthook

        def _sys_excepthook(
            exc_type: type,
            exc_value: BaseException,
            exc_tb: Optional[TracebackType],
        ) -> None:
            if not issubclass(exc_type, KeyboardInterrupt):
                self._on_exception(exc_type, exc_value, exc_tb)
            self._original_sys_hook(exc_type, exc_value, exc_tb)

        def _threading_excepthook(args: threading.ExceptHookArgs) -> None:
            if args.exc_type is not None and not issubclass(args.exc_type, SystemExit):
                self._on_exception(args.exc_type, args.exc_value, args.exc_traceback)
            self._original_threading_hook(args)

        sys.excepthook = _sys_excepthook
        threading.excepthook = _threading_excepthook
        self._installed = True

    def attach_asyncio_loop(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        target_loop = loop
        if target_loop is None:
            try:
                target_loop = asyncio.get_running_loop()
            except RuntimeError:
                return

        previous_handler = target_loop.get_exception_handler()

        def _async_exception_handler(
            current_loop: asyncio.AbstractEventLoop,
            context: dict[str, Any],
        ) -> None:
            exc = context.get("exception")
            if isinstance(exc, BaseException):
                self._on_exception(type(exc), exc, exc.__traceback__)
            if previous_handler is not None:
                previous_handler(current_loop, context)
            else:
                current_loop.default_exception_handler(context)

        target_loop.set_exception_handler(_async_exception_handler)

    def uninstall(self) -> None:
        if not self._installed:
            return
        sys.excepthook = self._original_sys_hook
        threading.excepthook = self._original_threading_hook
        self._installed = False