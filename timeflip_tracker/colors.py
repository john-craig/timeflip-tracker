from random import randrange

from colour import Color


def color_to_tuple(color):
    c = Color(color)

    color_tuple = (int(c.red * 255), int(c.blue * 255), int(c.green * 255))

    return color_tuple


def random_color_tuple():
    return (randrange(0, 255), randrange(0, 255), randrange(0, 255))
