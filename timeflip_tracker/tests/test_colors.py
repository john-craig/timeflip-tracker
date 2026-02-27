from timeflip_tracker import colors


def test_color_to_tuple_uses_module_color(monkeypatch):
    class DummyColor:
        def __init__(self, value):
            assert value == "my-color"
            self.red = 1.0
            self.blue = 0.5
            self.green = 0.0

    monkeypatch.setattr(colors, "Color", DummyColor)

    assert colors.color_to_tuple("my-color") == (255, 127, 0)


def test_random_color_tuple_draws_three_values(monkeypatch):
    values = iter([10, 20, 30])
    monkeypatch.setattr(colors, "randrange", lambda a, b: next(values))

    assert colors.random_color_tuple() == (10, 20, 30)
