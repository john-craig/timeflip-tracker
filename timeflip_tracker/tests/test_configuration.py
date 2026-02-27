from pathlib import Path

import pytest

from timeflip_tracker import configuration


def test_validate_configuration_rejects_no_devices():
    with pytest.raises(ValueError, match="No devices"):
        configuration.validate_configuration({"devices": []})


def test_validate_configuration_rejects_more_than_12_facets():
    cfg = {"devices": [{"name": "dev", "facets": [{"value": "x"}] * 13}]}

    with pytest.raises(ValueError, match="Too many facets"):
        configuration.validate_configuration(cfg)


def test_load_configuration_uses_default_path(monkeypatch, tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("ignored", encoding="utf-8")

    monkeypatch.setattr(configuration, "DEFAULT_CONFIG_PATH", str(config_file))
    monkeypatch.delenv("CONFIG_PATH", raising=False)

    loaded = {"devices": [{"name": "x", "facets": []}]}

    class DummyYaml:
        def load(self, file_obj):
            assert Path(file_obj.name) == config_file
            return loaded

    monkeypatch.setattr(configuration, "yaml", DummyYaml())

    result = configuration.load_configuration()

    assert result == loaded


def test_load_configuration_prefers_env_path(monkeypatch, tmp_path):
    config_file = tmp_path / "custom.yaml"
    config_file.write_text("ignored", encoding="utf-8")

    monkeypatch.setenv("CONFIG_PATH", str(config_file))

    loaded = {"devices": [{"name": "env-dev", "facets": []}]}

    class DummyYaml:
        def load(self, file_obj):
            assert file_obj.name == str(config_file)
            return loaded

    monkeypatch.setattr(configuration, "yaml", DummyYaml())

    result = configuration.load_configuration()

    assert result == loaded
