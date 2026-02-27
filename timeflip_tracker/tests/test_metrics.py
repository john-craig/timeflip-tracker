from timeflip_tracker import metrics


class Recorder:
    def __init__(self):
        self.payload = None

    def info(self, payload):
        self.payload = payload


def test_cut_timeflip_connection_info(monkeypatch):
    recorder = Recorder()
    monkeypatch.setattr(metrics, "timeflip_connection_info", recorder)

    metrics.cut_timeflip_connection_info("connected", "AA:BB")

    assert recorder.payload == {"state": "connected", "mac_address": "AA:BB"}


def test_cut_timeflip_status_info(monkeypatch):
    recorder = Recorder()
    monkeypatch.setattr(metrics, "timeflip_status_info", recorder)

    metrics.cut_timeflip_status_info("AA:BB", 77, "1.2.3", "TimeFlip")

    assert recorder.payload == {
        "mac_address": "AA:BB",
        "firmware_revision": 77,
        "battery_level": "1.2.3",
        "device_name": "TimeFlip",
    }


def test_cut_timeflip_facet_info(monkeypatch):
    recorder = Recorder()
    monkeypatch.setattr(metrics, "timeflip_facet_info", recorder)

    metrics.cut_timeflip_facet_info("iso", "dev", "AA", 2, "work")

    assert recorder.payload == {
        "time": "iso",
        "device_name": "dev",
        "mac_address": "AA",
        "facet_num": 2,
        "facet_value": "work",
    }
