from datetime import datetime, timezone
from types import TracebackType
from typing import Optional, Dict, Any, List

from .environment import collect_environment, EnvironmentDto
from .hooks import ExceptionHooksManager
from .stacktrace import normalize_exception, ExceptionDto


class Client:
    def __init__(
        self,
        project_key: str,
        app_version: str = "0.1.0",
        environment: str = "production",
        dsn: str = "http://localhost:8000/api/v1/crashes",
    ) -> None:
        if not project_key:
            raise ValueError("project_key is required to initialize TraceX Client")
        self.project_key = project_key
        self.app_version = app_version
        self.environment = environment
        self.dsn = dsn
        self.captured_events: List[Dict[str, Any]] = []

    def build_crash_payload(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Dict[str, Any]:
        env_dto: EnvironmentDto = collect_environment(self.app_version)
        exc_dto: ExceptionDto = normalize_exception(exc_type, exc_value, exc_tb)

        return {
            "project_key": self.project_key,
            "environment": self.environment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "exception": exc_dto.to_dict(),
            "device_environment": env_dto.to_dict(),
        }

    def capture_exception(
        self,
        exc_type: Optional[type] = None,
        exc_value: Optional[BaseException] = None,
        exc_tb: Optional[TracebackType] = None,
    ) -> Dict[str, Any]:
        payload = self.build_crash_payload(exc_type, exc_value, exc_tb)
        self.captured_events.append(payload)
        return payload


class Hub:
    _instance: Optional["Hub"] = None

    def __init__(self) -> None:
        self._client: Optional[Client] = None
        self._hooks_manager: Optional[ExceptionHooksManager] = None

    @classmethod
    def get_current(cls) -> "Hub":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def client(self) -> Optional[Client]:
        return self._client

    def bind_client(self, client: Client, install_hooks: bool = True) -> None:
        if self._hooks_manager is not None:
            self._hooks_manager.uninstall()

        self._client = client
        self._hooks_manager = ExceptionHooksManager(self._handle_uncaught_exception)
        if install_hooks:
            self._hooks_manager.install()
            self._hooks_manager.attach_asyncio_loop()

    def _handle_uncaught_exception(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self._client is not None:
            self._client.capture_exception(exc_type, exc_value, exc_tb)

    def capture_exception(self, exception: Optional[BaseException] = None) -> Optional[Dict[str, Any]]:
        if self._client is None:
            return None
        if exception is not None:
            return self._client.capture_exception(type(exception), exception, exception.__traceback__)
        import sys
        exc_type, exc_value, exc_tb = sys.exc_info()
        if exc_value is None:
            return None
        return self._client.capture_exception(exc_type, exc_value, exc_tb)

    def reset(self) -> None:
        if self._hooks_manager is not None:
            self._hooks_manager.uninstall()
        self._hooks_manager = None
        self._client = None