from typing import Optional, Dict, Any
from .client import Client, Hub

__version__ = "0.1.0"
__all__ = ["init", "capture_exception", "Client", "Hub"]


def init(
    project_key: str,
    app_version: str = "0.1.0",
    environment: str = "production",
    dsn: str = "http://localhost:8000/api/v1/crashes",
    install_hooks: bool = True,
) -> Client:
    client = Client(
        project_key=project_key,
        app_version=app_version,
        environment=environment,
        dsn=dsn,
    )
    Hub.get_current().bind_client(client, install_hooks=install_hooks)
    return client


def capture_exception(exception: Optional[BaseException] = None) -> Optional[Dict[str, Any]]:
    return Hub.get_current().capture_exception(exception)