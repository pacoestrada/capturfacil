"""Text selection, movement and reversible annotation history."""
from copy import deepcopy
import math
import cairo
from drawing import text_layout


class History:
    def __init__(self, limit=100):
        self.past = []
        self.future = []
        self.limit = limit

    def record(self, marks):
        self.past.append(deepcopy(marks))
        del self.past[:-self.limit]
        self.future.clear()

    def undo(self, marks):
        if not self.past:
            return marks
        self.future.append(deepcopy(marks))
        return self.past.pop()

    def redo(self, marks):
        if not self.future:
            return marks
        self.past.append(deepcopy(marks))
        return self.future.pop()


def text_bounds(mark):
    cr = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
    layout = text_layout(cr, mark)
    ink, logical = layout.get_pixel_extents()
    left, top = min(ink.x, logical.x), min(ink.y, logical.y)
    right = max(ink.x + ink.width, logical.x + logical.width)
    bottom = max(ink.y + ink.height, logical.y + logical.height)
    x, y = mark['points'][0]
    return x + left, y + top, max(1, right-left), max(1, bottom-top)


def hit_text(marks, point, tolerance=4):
    px, py = point
    for index in range(len(marks)-1, -1, -1):
        if marks[index]['kind'] != 'text':
            continue
        x, y, width, height = text_bounds(marks[index])
        if x-tolerance <= px <= x+width+tolerance and y-tolerance <= py <= y+height+tolerance:
            return index
    return None


def move_text(mark, dx, dy, image_width, image_height):
    """Translate from the drag-start mark, clamped to the image, not incrementally."""
    result = deepcopy(mark)
    x, y, width, height = bounds(mark)
    new_x = min(max(0, x + dx), max(0, image_width-width))
    new_y = min(max(0, y + dy), max(0, image_height-height))
    result['points'] = [(px + new_x-x, py + new_y-y) for px, py in mark['points']]
    return result


def bounds(mark):
    if mark['kind'] == 'text':
        return text_bounds(mark)
    xs, ys = zip(*mark['points'])
    return min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys)


def hit_mark(marks, point, tolerance=4):
    px, py = point
    for index in range(len(marks)-1, -1, -1):
        if marks[index]['kind'] in ('arrow', 'line', 'dots'):
            a, b = marks[index]['points'][0], marks[index]['points'][-1]
            dx, dy = b[0]-a[0], b[1]-a[1]
            length2 = dx*dx + dy*dy
            t = min(1, max(0, ((px-a[0])*dx+(py-a[1])*dy)/length2)) if length2 else 0
            if math.hypot(px-a[0]-t*dx, py-a[1]-t*dy) <= tolerance + marks[index]['width']/2:
                return index
            continue
        if marks[index]['kind'] not in ('text', 'rect', 'ellipse', 'pen'):
            continue
        x, y, w, h = bounds(marks[index])
        if x-tolerance <= px <= x+w+tolerance and y-tolerance <= py <= y+h+tolerance:
            return index
    return None


def handles(mark):
    if mark['kind'] in ('arrow', 'line', 'dots'):
        return [mark['points'][0], mark['points'][-1]]
    if mark['kind'] not in ('rect', 'ellipse', 'pen'):
        return []
    x, y, w, h = bounds(mark)
    return [(x,y), (x+w,y), (x+w,y+h), (x,y+h)]


def hit_handle(mark, point, tolerance):
    for i, (x,y) in enumerate(handles(mark)):
        if abs(point[0]-x) <= tolerance and abs(point[1]-y) <= tolerance:
            return i
    return None


def resize(mark, corner, point, image_width, image_height):
    result = deepcopy(mark)
    x = min(max(0, point[0]), image_width-1)
    y = min(max(0, point[1]), image_height-1)
    if mark['kind'] in ('arrow', 'line', 'dots'):
        opposite = mark['points'][1-corner]
        if math.dist((x,y), opposite) >= 1:
            result['points'][corner] = (x,y)
        return result
    opposite = handles(mark)[(corner+2)%4]
    # Keep a drawable shape, including when the pointer crosses its opposite corner.
    if abs(x-opposite[0]) < 1:
        x = opposite[0]+1 if opposite[0] < image_width-1 else opposite[0]-1
    if abs(y-opposite[1]) < 1:
        y = opposite[1]+1 if opposite[1] < image_height-1 else opposite[1]-1
    if mark['kind'] == 'pen':
        dragged = handles(mark)[corner]
        sx = (x-opposite[0]) / (dragged[0]-opposite[0]) if dragged[0] != opposite[0] else 1
        sy = (y-opposite[1]) / (dragged[1]-opposite[1]) if dragged[1] != opposite[1] else 1
        result['points'] = [(opposite[0]+(px-opposite[0])*sx, opposite[1]+(py-opposite[1])*sy) for px,py in mark['points']]
    else:
        result['points'] = [opposite, (x,y)]
    return result
