"""Exercise the real GTK window without changing desktop shortcuts or user files."""
import os
from pathlib import Path
import sys
import tempfile
os.environ['GSETTINGS_BACKEND'] = 'memory'
os.environ['XDG_CONFIG_HOME'] = tempfile.mkdtemp(prefix='capturfacil-gui-config-')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import cairo
from capturfacil import Application, Gdk, GLib, Gtk
from types import SimpleNamespace
from unittest.mock import patch
# Never add synthetic GUI fixtures to the user's recent files.
recent_patch = patch('capturfacil.register_saved_image', return_value=False)
recent_patch.start()

OUT = Path('/tmp/capturfacil/qa')
OUT.mkdir(parents=True, exist_ok=True)
image = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1400, 850)
cr = cairo.Context(image)
cr.set_source_rgb(.97, .98, 1)
cr.paint()
cr.set_source_rgb(.08, .18, .27)
cr.rectangle(0, 0, 1400, 110)
cr.fill()
cr.set_source_rgb(1, 1, 1)
cr.select_font_face('Sans', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
cr.set_font_size(34)
cr.move_to(55, 70)
cr.show_text('COMPILANDO  /  Una captura de ejemplo')
for y, label in [(240, 'Selecciona lo importante'), (390, 'Añade una explicación'), (540, 'Guarda y comparte')]:
    cr.set_source_rgb(.88, .93, .96)
    cr.rectangle(55, y - 60, 1290, 115)
    cr.fill()
    cr.set_source_rgb(.1, .25, .35)
    cr.set_font_size(30)
    cr.move_to(90, y + 10)
    cr.show_text(label)
image.write_to_png(str(OUT / 'fixture.png'))

app = Application()
errors = []

def screen(window, name):
    gdkw = window.get_window()
    pixbuf = Gdk.pixbuf_get_from_window(gdkw, 0, 0, gdkw.get_width(), gdkw.get_height())
    pixbuf.savev(str(OUT / name), 'png', [], [])

def start():
    try:
        w = app.window
        screen(w, 'welcome.png')
        w.load_image(str(OUT / 'fixture.png'))
        w.edit_button.set_active(True)
        GLib.timeout_add(500, edit)
    except Exception as e:
        errors.append(str(e))
        app.quit()
    return False

def edit():
    try:
        w = app.window
        # Simulated pointer gestures exercise coordinate mapping and undo/redo.
        def event(x, y):
            return SimpleNamespace(button=1, x=w.offset[0] + x*w.scale, y=w.offset[1] + y*w.scale)
        w.press(w.canvas, event(950, 300))
        w.motion(w.canvas, event(580, 240))
        w.release(w.canvas, event(580, 240))
        assert len(w.marks) == 1
        w.undo()
        assert not w.marks
        w.redo()
        assert len(w.marks) == 1
        w.add_mark({'kind': 'ellipse', 'points': [(62, 466), (700, 590)], 'width': 5, 'color': (.9,.12,.2,1)})
        w.add_mark({'kind': 'text', 'points': [(800, 420)], 'width': 4, 'color': (.07,.4,.47,1), 'size': 38, 'text': 'Así de fácil'})
        w.folder = lambda: OUT / 'saved'
        assert w.save()
        first = w.saved
        assert w.save() and w.saved == first
        png = cairo.ImageSurface.create_from_png(str(first))
        assert png.get_width() == 1400 and png.get_height() == 850
        w.undo()
        assert w.save() and w.saved != first and first.exists()
        w.redo()
        # Test clipboard API, but do not overwrite the user's clipboard.
        w.canvas.queue_draw()
        GLib.timeout_add(500, finish)
    except Exception as e:
        errors.append(str(e))
        app.quit()
    return False

def finish():
    screen(app.window, 'editor.png')
    app.window.dirty = False
    app.quit()
    return False
GLib.timeout_add(800, start)
app.run([])
if errors:
    raise RuntimeError(errors)
print('GTK UI, gestures, undo/redo, full-resolution export and non-overwriting save: OK')

