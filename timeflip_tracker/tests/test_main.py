import asyncio

from timeflip_tracker import main


class DummyLogger:
    def warning(self, msg):
        return None


def test_run_main_calls_asyncio_run(monkeypatch):
    called = []
    monkeypatch.setattr(main.asyncio, "run", lambda coro: called.append(coro))

    main.run_main()

    assert len(called) == 1
    called[0].close()


def test_main_initializes_and_gathers(monkeypatch):
    monkeypatch.setattr(main, "create_logger", lambda: None)
    monkeypatch.setattr(main, "get_logger", lambda: DummyLogger())
    monkeypatch.setattr(main, "connect_database", lambda: object())

    config = {
        "adapter": "AA:BB",
        "devices": [
            {"name": "dev1", "mac_address": "1", "password": "p", "facets": []},
            {"name": "dev2", "mac_address": "2", "password": "p", "facets": []},
        ],
    }
    monkeypatch.setattr(main, "load_configuration", lambda: config)

    connect_calls = []

    async def fake_connect_and_run(device_config, adapter_addr=None):
        connect_calls.append((device_config["name"], adapter_addr))
        return None

    monkeypatch.setattr(main, "connect_and_run", fake_connect_and_run)

    gathered = []

    async def fake_gather(*cors):
        for coro in cors:
            gathered.append(coro)
            await coro
        return []

    monkeypatch.setattr(main.asyncio, "gather", fake_gather)
    monkeypatch.setattr(main.signal, "signal", lambda *args: None)

    shutdown_calls = []

    class Server:
        def shutdown(self):
            shutdown_calls.append("shutdown")

    monkeypatch.setattr(main, "start_http_server", lambda port: (Server(), None))
    monkeypatch.setattr(main.asyncio, "all_tasks", lambda loop: [])
    monkeypatch.setattr(main, "close_database", lambda: shutdown_calls.append("db"))

    asyncio.run(main.main())

    assert connect_calls == [("dev1", "AA:BB"), ("dev2", "AA:BB")]
    assert len(gathered) == 2
