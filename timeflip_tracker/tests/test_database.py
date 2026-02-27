import datetime

from timeflip_tracker import database


class DummyLogger:
    def __init__(self):
        self.messages = []

    def info(self, msg):
        self.messages.append(("info", msg))

    def debug(self, msg):
        self.messages.append(("debug", msg))


class FakeCursor:
    def __init__(self):
        self.executed = []
        self.fetchall_result = []
        self.raise_interface_error_once = False
        self._raised = False

    def execute(self, statement):
        if self.raise_interface_error_once and not self._raised:
            self._raised = True
            raise database.mariadb.InterfaceError("connection dropped")
        self.executed.append(statement)

    def fetchall(self):
        return self.fetchall_result


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.reconnect_called = 0
        self.commit_called = 0
        self.closed = False

    def cursor(self):
        return self._cursor

    def reconnect(self):
        self.reconnect_called += 1

    def commit(self):
        self.commit_called += 1

    def close(self):
        self.closed = True


def reset_database_globals():
    database.database_connection = None
    database.database_cursor = None


def test_connect_database_returns_none_when_required_env_missing(monkeypatch):
    reset_database_globals()
    monkeypatch.delenv("MARIADB_HOST", raising=False)
    monkeypatch.delenv("MARIADB_USER", raising=False)
    monkeypatch.delenv("MARIADB_PASSWORD", raising=False)
    monkeypatch.setattr(database, "get_logger", lambda: DummyLogger())

    assert database.connect_database() is None


def test_connect_database_creates_table(monkeypatch):
    reset_database_globals()
    monkeypatch.setenv("MARIADB_HOST", "db")
    monkeypatch.setenv("MARIADB_USER", "user")
    monkeypatch.setenv("MARIADB_PASSWORD", "pass")
    monkeypatch.setenv("MARIADB_PORT", "3308")
    monkeypatch.setenv("MARIADB_DATABASE", "timeflip_test")

    logger = DummyLogger()
    cursor = FakeCursor()
    conn = FakeConnection(cursor)

    kwargs_seen = {}

    def fake_connect(**kwargs):
        kwargs_seen.update(kwargs)
        return conn

    monkeypatch.setattr(database, "get_logger", lambda: logger)
    monkeypatch.setattr(database.mariadb, "connect", fake_connect)

    result_cursor = database.connect_database()

    assert result_cursor is cursor
    assert kwargs_seen == {
        "host": "db",
        "port": 3308,
        "user": "user",
        "password": "pass",
        "database": "timeflip_test",
    }
    assert any("CREATE TABLE IF NOT EXISTS timeflip_events" in stmt for stmt in cursor.executed)


def test_close_database_closes_connection():
    cursor = FakeCursor()
    conn = FakeConnection(cursor)
    database.database_connection = conn

    database.close_database()

    assert conn.closed is True


def test_get_prev_event_returns_latest_row(monkeypatch):
    logger = DummyLogger()
    cursor = FakeCursor()
    row = (1, "a", "b", "dev", "AA", 2, "focus")
    cursor.fetchall_result = [row]
    conn = FakeConnection(cursor)

    database.database_connection = conn
    database.database_cursor = cursor
    monkeypatch.setattr(database, "get_logger", lambda: logger)

    assert database.get_prev_event() == row


def test_get_prev_event_reconnects_on_interface_error(monkeypatch):
    logger = DummyLogger()
    cursor = FakeCursor()
    cursor.raise_interface_error_once = True
    row = (1,)
    cursor.fetchall_result = [row]
    conn = FakeConnection(cursor)

    database.database_connection = conn
    database.database_cursor = cursor
    monkeypatch.setattr(database, "get_logger", lambda: logger)

    assert database.get_prev_event() == row
    assert conn.reconnect_called == 1


def test_update_event_end_noop_without_connection():
    database.database_connection = None
    database.database_cursor = None

    assert database.update_event_end(1, "2020-01-01T00:00:00") is None


def test_insert_event_skips_duplicate_event(monkeypatch):
    logger = DummyLogger()
    cursor = FakeCursor()
    conn = FakeConnection(cursor)

    database.database_connection = conn
    database.database_cursor = cursor

    prev = (10, None, None, "dev", "AA", 3, "work")
    monkeypatch.setattr(database, "get_prev_event", lambda: prev)
    monkeypatch.setattr(database, "get_logger", lambda: logger)

    cut_calls = []
    monkeypatch.setattr(database, "cut_timeflip_facet_info", lambda *args: cut_calls.append(args))

    database.insert_event("dev", "AA", 3, "work", (1, 2, 3))

    assert conn.commit_called == 0
    assert not any("INSERT INTO timeflip_events" in stmt for stmt in cursor.executed)
    assert cut_calls == []


def test_insert_event_updates_previous_and_inserts(monkeypatch):
    logger = DummyLogger()
    cursor = FakeCursor()
    conn = FakeConnection(cursor)

    database.database_connection = conn
    database.database_cursor = cursor

    prev = (10, None, None, "dev", "AA", 1, "old")
    monkeypatch.setattr(database, "get_prev_event", lambda: prev)
    monkeypatch.setattr(database, "get_logger", lambda: logger)

    update_calls = []
    monkeypatch.setattr(database, "update_event_end", lambda event_id, end: update_calls.append((event_id, end)))

    cut_calls = []
    monkeypatch.setattr(database, "cut_timeflip_facet_info", lambda *args: cut_calls.append(args))

    class FixedDatetime(datetime.datetime):
        @classmethod
        def now(cls):
            return cls(2024, 1, 2, 3, 4, 5)

    monkeypatch.setattr(database.datetime, "datetime", FixedDatetime)

    database.insert_event("dev", "AA", 2, "new", (9, 8, 7))

    assert update_calls and update_calls[0][0] == 10
    assert len(cut_calls) == 1
    assert conn.commit_called == 1
    assert any("INSERT INTO timeflip_events" in stmt for stmt in cursor.executed)
