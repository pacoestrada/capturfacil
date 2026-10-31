"""Lossless temporary screenshot exchange, keeping GNOME as the capture backend."""
import gi
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gdk, GdkPixbuf
import cairo


def temporary_suffix(mode):
    # Window captures may contain transparency; retain PNG for those and areas.
    if mode in ('monitor', 'screen'):
        if any(f.get_name() == 'bmp' and f.is_writable() for f in GdkPixbuf.Pixbuf.get_formats()):
            return '.bmp'
    return '.png'


def load_surface(path):
    if str(path).lower().endswith('.png'):
        return cairo.ImageSurface.create_from_png(str(path))
    pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(path))
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, pixbuf.get_width(), pixbuf.get_height())
    cr = cairo.Context(surface)
    Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
    cr.paint()
    return surface
