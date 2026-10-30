"""Rendering in original image coordinates, shared by preview and export."""
import math
import cairo
import gi
gi.require_version('PangoCairo', '1.0')
gi.require_version('Pango', '1.0')
from gi.repository import Pango, PangoCairo


def draw_mark(cr, mark):
    kind = mark['kind']
    points = mark['points']
    x, y = points[0]
    ex, ey = points[-1]
    width = mark['width']
    cr.save()
    cr.set_source_rgba(*mark['color'])
    cr.set_line_width(width)
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)
    if kind == 'text':
        layout = PangoCairo.create_layout(cr)
        font = Pango.FontDescription('Sans Bold')
        font.set_absolute_size(mark.get('size', 28) * Pango.SCALE)
        layout.set_font_description(font)
        layout.set_text(mark.get('text', ''), -1)
        cr.move_to(x, y)
        PangoCairo.show_layout(cr, layout)
    elif kind == 'ellipse':
        rx, ry = abs(ex - x) / 2, abs(ey - y) / 2
        if rx > 0.5 and ry > 0.5:
            cr.save()
            cr.translate((x + ex) / 2, (y + ey) / 2)
            cr.scale(rx, ry)
            cr.arc(0, 0, 1, 0, math.tau)
            cr.restore()
            cr.stroke()
    elif kind == 'rect':
        cr.rectangle(min(x, ex), min(y, ey), abs(ex - x), abs(ey - y))
        cr.stroke()
    else:
        if kind == 'dots':
            cr.set_dash([0.1, width * 2.8])
        cr.move_to(x, y)
        for px, py in points[1:]:
            cr.line_to(px, py)
        cr.stroke()
        if kind == 'pen' and len(points) == 1:
            cr.arc(x, y, width / 2, 0, math.tau)
            cr.fill()
        if kind == 'arrow' and math.hypot(ex - x, ey - y) > 1:
            angle = math.atan2(ey - y, ex - x)
            length = max(14, width * 4)
            cr.move_to(ex - length * math.cos(angle - 0.48), ey - length * math.sin(angle - 0.48))
            cr.line_to(ex, ey)
            cr.line_to(ex - length * math.cos(angle + 0.48), ey - length * math.sin(angle + 0.48))
            cr.stroke()
    cr.restore()


def render(base, marks):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, base.get_width(), base.get_height())
    cr = cairo.Context(surface)
    cr.set_source_surface(base, 0, 0)
    cr.paint()
    for mark in marks:
        draw_mark(cr, mark)
    return surface
