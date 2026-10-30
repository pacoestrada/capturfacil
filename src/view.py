"""Geometry for zooming and cropping a monitor from an X11 desktop capture."""
import math
import cairo


def fit_scale(image_width, image_height, viewport_width, viewport_height):
    return max(0.01, min((viewport_width - 36) / image_width,
                         (viewport_height - 36) / image_height, 4.0))


def monitor_crop(base, monitor, desktop):
    mx, my, mw, mh = monitor
    dx, dy, dw, dh = desktop
    sx, sy = base.get_width() / dw, base.get_height() / dh
    left = max(0, round((mx - dx) * sx))
    top = max(0, round((my - dy) * sy))
    right = min(base.get_width(), round((mx + mw - dx) * sx))
    bottom = min(base.get_height(), round((my + mh - dy) * sy))
    if right <= left or bottom <= top:
        raise ValueError('No se ha podido delimitar el monitor actual.')
    result = cairo.ImageSurface(cairo.FORMAT_ARGB32, right - left, bottom - top)
    cr = cairo.Context(result)
    cr.set_source_surface(base, -left, -top)
    cr.paint()
    return result
