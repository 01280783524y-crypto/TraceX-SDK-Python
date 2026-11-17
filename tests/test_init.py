import pytest
import tracex
from tracex.client import Hub


def setup_function() -> None:
    Hub.get_current().reset()


def test_init_configures_client_and_environment() -> None:
    client = tracex.init(
        project_key="proj_test_123",
        app_version="1.2.3",
        environment="staging",
        install_hooks=False,
    )

    assert client.project_key == "proj_test_123"
    assert client.app_version == "1.2.3"
    assert client.environment == "staging"

    try:
        raise ValueError("Sample initialization error")
    except ValueError as err:
        payload = tracex.capture_exception(err)

    assert payload is not None
    assert payload["project_key"] == "proj_test_123"
    assert payload["environment"] == "staging"
    assert payload["exception"]["error_type"] == "ValueError"
    assert payload["exception"]["message"] == "Sample initialization error"
    assert len(payload["exception"]["frames"]) > 0

    env = payload["device_environment"]
    assert env["app_version"] == "1.2.3"
    assert env["os_name"] != ""
    assert env["os_version"] != ""
    assert env["device_model"] != ""
    assert env["runtime_version"] != ""
    assert isinstance(env["process_ram_mb"], float)


def test_init_requires_project_key() -> None:
    with pytest.raises(ValueError):
        tracex.init(project_key="", install_hooks=False)