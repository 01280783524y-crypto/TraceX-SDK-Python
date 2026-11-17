import asyncio
import sys
import threading
import tracex
from tracex.client import Hub


def setup_function() -> None:
    Hub.get_current().reset()


def test_sys_excepthook_traps_unhandled_exception() -> None:
    original_hook = sys.excepthook
    try:
        client = tracex.init(project_key="proj_hooks_1", app_version="2.0.0", install_hooks=True)

        try:
            1 / 0
        except ZeroDivisionError as exc:
            sys.excepthook(type(exc), exc, exc.__traceback__)

        assert len(client.captured_events) == 1
        event = client.captured_events[0]
        assert event["exception"]["error_type"] == "ZeroDivisionError"
    finally:
        Hub.get_current().reset()
        sys.excepthook = original_hook


def test_threading_excepthook_traps_thread_crash() -> None:
    client = tracex.init(project_key="proj_hooks_2", app_version="2.0.0", install_hooks=True)

    def worker() -> None:
        raise RuntimeError("Thread exploded")

    t = threading.Thread(target=worker)
    t.start()
    t.join()

    assert len(client.captured_events) == 1
    assert client.captured_events[0]["exception"]["error_type"] == "RuntimeError"
    assert client.captured_events[0]["exception"]["message"] == "Thread exploded"


def test_asyncio_exception_handler_traps_async_crash() -> None:
    async def run_test() -> None:
        client = tracex.init(project_key="proj_hooks_3", app_version="2.0.0", install_hooks=True)

        async def failing_task() -> None:
            raise KeyError("missing_key")

        task = asyncio.create_task(failing_task())
        try:
            await task
        except KeyError:
            pass

        loop = asyncio.get_running_loop()
        loop.call_exception_handler({"message": "Async crash", "exception": KeyError("async_boom")})

        assert len(client.captured_events) == 1
        assert client.captured_events[0]["exception"]["error_type"] == "KeyError"

    asyncio.run(run_test())