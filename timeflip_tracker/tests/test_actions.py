from timeflip_tracker import actions


def test_invoke_hook_builds_shell_command_and_logs(monkeypatch):
    logs = []

    class DummyLogger:
        def info(self, msg):
            logs.append(("info", msg))

        def warning(self, msg):
            logs.append(("warning", msg))

    class Result:
        returncode = 0

    calls = []
    monkeypatch.setattr(actions, "get_logger", lambda: DummyLogger())
    monkeypatch.setattr(actions.subprocess, "run", lambda cmd, shell: calls.append((cmd, shell)) or Result())

    actions.invoke_hook("echo", ["one", "two"])

    assert calls == [("echo 'one' 'two'", True)]
    assert any("Invoking hook 'echo'" in msg for level, msg in logs if level == "info")


def test_invoke_hook_warns_on_nonzero_exit(monkeypatch):
    warnings = []

    class DummyLogger:
        def info(self, msg):
            return None

        def warning(self, msg):
            warnings.append(msg)

    class Result:
        returncode = 1

    monkeypatch.setattr(actions, "get_logger", lambda: DummyLogger())
    monkeypatch.setattr(actions.subprocess, "run", lambda cmd, shell: Result())

    actions.invoke_hook("false", [])

    assert warnings == ["Hook 'false' failed"]
