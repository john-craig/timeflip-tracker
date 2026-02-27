import sys
import types


# Provide lightweight stubs for optional runtime dependencies so unit tests
# can import modules without real services/hardware.
if "colour" not in sys.modules:
    colour_mod = types.ModuleType("colour")

    class Color:
        def __init__(self, value):
            palette = {
                "white": (1.0, 1.0, 1.0),
                "red": (1.0, 0.0, 0.0),
                "green": (0.0, 1.0, 0.0),
                "blue": (0.0, 0.0, 1.0),
            }
            self.red, self.green, self.blue = palette.get(value, (0.5, 0.5, 0.5))

    colour_mod.Color = Color
    sys.modules["colour"] = colour_mod

if "ruamel" not in sys.modules:
    ruamel_mod = types.ModuleType("ruamel")
    yaml_pkg = types.ModuleType("ruamel.yaml")

    class YAML:
        def __init__(self, typ=None):
            self.typ = typ

        def load(self, file_obj):
            return {}

    yaml_pkg.YAML = YAML
    ruamel_mod.yaml = yaml_pkg
    sys.modules["ruamel"] = ruamel_mod
    sys.modules["ruamel.yaml"] = yaml_pkg

if "mariadb" not in sys.modules:
    mariadb_mod = types.ModuleType("mariadb")

    class InterfaceError(Exception):
        pass

    def connect(**kwargs):  # pragma: no cover - overridden in tests
        raise RuntimeError("connect should be mocked in tests")

    mariadb_mod.InterfaceError = InterfaceError
    mariadb_mod.connect = connect
    sys.modules["mariadb"] = mariadb_mod

if "prometheus_client" not in sys.modules:
    prom_mod = types.ModuleType("prometheus_client")

    class Info:
        def __init__(self, name, description):
            self.name = name
            self.description = description
            self.data = None

        def info(self, data):
            self.data = data

    class _Server:
        def shutdown(self):
            return None

    def start_http_server(port):
        return _Server(), None

    prom_mod.Info = Info
    prom_mod.start_http_server = start_http_server
    sys.modules["prometheus_client"] = prom_mod

if "bleak" not in sys.modules:
    bleak_mod = types.ModuleType("bleak")

    class BleakError(Exception):
        pass

    class BleakClient:
        def __init__(self, device):
            self.device = device

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def read_gatt_char(self, characteristic):
            return b""

    class BleakScanner:
        @staticmethod
        async def discover():
            return []

    class BleakGATTCharacteristic:
        pass

    bleak_mod.BleakError = BleakError
    bleak_mod.BleakClient = BleakClient
    bleak_mod.BleakScanner = BleakScanner
    bleak_mod.BleakGATTCharacteristic = BleakGATTCharacteristic
    sys.modules["bleak"] = bleak_mod

    backends_pkg = types.ModuleType("bleak.backends")
    device_mod = types.ModuleType("bleak.backends.device")

    class BLEDevice:
        pass

    device_mod.BLEDevice = BLEDevice
    backends_pkg.device = device_mod
    sys.modules["bleak.backends"] = backends_pkg
    sys.modules["bleak.backends.device"] = device_mod

if "bluetooth_adapters" not in sys.modules:
    bt_mod = types.ModuleType("bluetooth_adapters")

    class _Adapters:
        def __init__(self):
            self.adapters = {}

        async def refresh(self):
            return None

    def get_adapters():
        return _Adapters()

    bt_mod.get_adapters = get_adapters
    sys.modules["bluetooth_adapters"] = bt_mod

if "pytimefliplib" not in sys.modules:
    pytimefliplib_mod = types.ModuleType("pytimefliplib")
    async_client_mod = types.ModuleType("pytimefliplib.async_client")

    class TimeFlipRuntimeError(Exception):
        pass

    class AsyncClient:
        def __init__(self, *args, **kwargs):
            self.address = args[0] if args else ""

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    async_client_mod.CHARACTERISTICS = {"facet": "facet-char"}
    async_client_mod.DEFAULT_PASSWORD = "0000"
    async_client_mod.AsyncClient = AsyncClient
    async_client_mod.TimeFlipRuntimeError = TimeFlipRuntimeError

    pytimefliplib_mod.async_client = async_client_mod

    sys.modules["pytimefliplib"] = pytimefliplib_mod
    sys.modules["pytimefliplib.async_client"] = async_client_mod

if "requests" not in sys.modules:
    requests_mod = types.ModuleType("requests")
    sys.modules["requests"] = requests_mod
