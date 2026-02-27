import asyncio

import pytest

from timeflip_tracker import connection


class DummyLogger:
    def __init__(self):
        self.messages = []

    def info(self, msg):
        self.messages.append(("info", msg))

    def debug(self, msg):
        self.messages.append(("debug", msg))

    def warning(self, msg):
        self.messages.append(("warning", msg))

    def error(self, msg):
        self.messages.append(("error", msg))


class DummyClient:
    def __init__(self):
        self.address = "AA:BB"
        self.colors = []
        self.notify_callback = None

    async def set_color(self, i, color):
        self.colors.append((i, color))

    async def register_notify_facet_v3(self, callback):
        self.notify_callback = callback

    async def current_facet(self):
        return 1

    async def firmware_revision(self):
        return "1.0"

    async def battery_level(self):
        return 88

    async def device_name(self):
        return "TF"


class StopLoop(Exception):
    pass


def test_timeflip_status_records_metrics(monkeypatch):
    logger = DummyLogger()
    client = DummyClient()
    calls = []

    monkeypatch.setattr(connection, "get_logger", lambda: logger)
    monkeypatch.setattr(connection, "cut_timeflip_status_info", lambda *args: calls.append(args))

    asyncio.run(connection.timeflip_status(client))

    assert calls == [("AA:BB", "1.0", 88, "TF")]


def test_actions_on_client_sets_colors_and_inserts_event(monkeypatch):
    logger = DummyLogger()
    client = DummyClient()

    monkeypatch.setattr(connection, "get_logger", lambda: logger)
    async def fake_timeflip_status(_client):
        return None

    monkeypatch.setattr(connection, "timeflip_status", fake_timeflip_status)
    monkeypatch.setattr(connection, "color_to_tuple", lambda value: (1, 2, 3) if value == "white" else (4, 5, 6))
    monkeypatch.setattr(connection, "random_color_tuple", lambda: (9, 9, 9))

    inserted = []
    monkeypatch.setattr(connection, "insert_event", lambda *args: inserted.append(args))
    hook_calls = []
    monkeypatch.setattr(connection, "invoke_hook", lambda *args: hook_calls.append(args))

    async def stop_sleep(_seconds):
        raise StopLoop

    monkeypatch.setattr(connection.asyncio, "sleep", stop_sleep)

    device_config = {
        "name": "dev1",
        "mac_address": "AA:BB",
        "password": "0000",
        "facets": [{"value": "work", "color": "red"}],
    }

    with pytest.raises(StopLoop):
        asyncio.run(connection.actions_on_client(device_config, client))

    assert len(client.colors) == 12
    assert client.colors[0] == (0, (4, 5, 6))
    assert inserted == [("dev1", "AA:BB", 1, "unassigned", (1, 2, 3))]
    assert hook_calls == []


def test_connect_and_run_resolves_adapter_and_invokes_connect_hook(monkeypatch):
    logger = DummyLogger()
    monkeypatch.setattr(connection, "get_logger", lambda: logger)

    metric_calls = []
    monkeypatch.setattr(connection, "cut_timeflip_connection_info", lambda *args: metric_calls.append(args))

    hook_calls = []
    monkeypatch.setattr(connection, "invoke_hook", lambda *args: hook_calls.append(args))

    action_calls = []

    async def fake_actions_on_client(device_config, client):
        action_calls.append((device_config["name"], client.address))
        raise connection.BleakError("stop")

    monkeypatch.setattr(connection, "actions_on_client", fake_actions_on_client)

    class Adapters:
        def __init__(self):
            self.adapters = {"hci0": {"address": "11:22"}, "hci1": {"address": "AA:AA"}}

        async def refresh(self):
            return None

    monkeypatch.setattr(connection, "get_adapters", lambda: Adapters())

    async def stop_sleep(_seconds):
        raise StopLoop

    monkeypatch.setattr(connection.asyncio, "sleep", stop_sleep)

    seen_kwargs = {}

    class FakeAsyncClient:
        def __init__(self, address, disconnected_callback=None, adapter=None):
            seen_kwargs["address"] = address
            seen_kwargs["adapter"] = adapter
            self.address = address
            self.disconnected_callback = disconnected_callback

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def setup(self, password):
            seen_kwargs["password"] = password

    monkeypatch.setattr(connection, "AsyncClient", FakeAsyncClient)

    cfg = {
        "name": "dev",
        "mac_address": "CC:DD",
        "password": "0000",
        "actions": {"on_connect": "echo connect"},
        "facets": [],
    }

    with pytest.raises(StopLoop):
        asyncio.run(connection.connect_and_run(cfg, adapter_addr="11:22"))

    assert seen_kwargs["address"] == "CC:DD"
    assert seen_kwargs["adapter"] == "hci0"
    assert seen_kwargs["password"] == "0000"
    assert any(call[0] == "connected" for call in metric_calls)
    assert hook_calls and hook_calls[0][0] == "echo connect"
    assert action_calls == [("dev", "CC:DD")]
