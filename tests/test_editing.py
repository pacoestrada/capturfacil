from copy import deepcopy
from pathlib import Path
import sys
from types import SimpleNamespace, MethodType
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import cairo
from capturfacil import Window, Gtk, Gdk, CSS
from drawing import render
from editing import History, hit_text, text_bounds, move_text


def mark(x=100, y=80, text='Texto aquí'):
    return {'kind':'text', 'points':[(x,y)], 'width':4,
            'color':(1,0,0,1), 'size':30, 'text':text}


class EditingTests(unittest.TestCase):
    def test_hit_selects_topmost_text_with_multiline_bounds(self):
        lower = mark(text='Primera línea\nSegunda línea')
        upper = mark()
        self.assertEqual(hit_text([lower, upper], (110,90)), 1)
        self.assertIsNone(hit_text([lower], (900,900)))
        self.assertGreater(text_bounds(lower)[3], text_bounds(upper)[3])

    def test_movement_clamps_to_image_without_changing_content(self):
        source = mark()
        result = move_text(source, 9999, 9999, 600, 400)
        x,y,w,h = text_bounds(result)
        self.assertLessEqual(x+w, 600)
        self.assertLessEqual(y+h, 400)
        self.assertEqual(source['points'], [(100,80)])
        self.assertEqual(result['text'], source['text'])
        result = move_text(source, -9999, -9999, 600, 400)
        self.assertEqual(text_bounds(result)[:2], (0,0))

    def test_history_restores_creation_movement_and_redo(self):
        history = History()
        history.record([])
        marks = [mark()]
        history.record(marks)
        moved = [move_text(marks[0], 50, 30, 600, 400)]
        self.assertEqual(history.undo(moved), marks)
        self.assertEqual(history.undo(marks), [])
        self.assertEqual(history.redo([]), marks)
        self.assertEqual(history.redo(marks), moved)
        history.undo(moved)
        history.record([mark(text='Otra edición')])
        self.assertEqual(history.future, [])

    def make_editor(self, scale):
        canvas = SimpleNamespace(grab_focus=lambda:None, queue_draw=lambda:None)
        editor = SimpleNamespace(base=cairo.ImageSurface(cairo.FORMAT_ARGB32,600,400),
                   marks=[mark()], history=History(), scale=scale, offset=(18,18),
                   tool='move', selected=None, moving=None, pan=None, current=None,
                   canvas=canvas, dirty=False, edit_button=SimpleNamespace(get_active=lambda:True),
                   update_buttons=lambda:None, set_status=lambda _:None, sync_style=lambda:None)
        for method in ['point','press','motion','release','changed','undo','redo','keypress']:
            setattr(editor, method, MethodType(getattr(Window, method), editor))
        return editor

    def event(self, scale, x, y):
        return SimpleNamespace(button=1, x=x*scale+18, y=y*scale+18)

    def test_drag_at_different_zoom_levels_and_undo(self):
        for scale in [.2,.5,1,2,4]:
            editor=self.make_editor(scale)
            original=deepcopy(editor.marks)
            editor.press(None,self.event(scale,110,90))
            self.assertEqual(editor.selected,0)
            editor.motion(None,self.event(scale,135,105))
            editor.release(None,self.event(scale,160,120))
            self.assertEqual(editor.marks[0]['points'],[(150,110)])
            self.assertEqual(len(editor.history.past),1)
            self.assertTrue(editor.dirty)
            editor.undo()
            self.assertEqual(editor.marks,original)
            editor.redo()
            self.assertEqual(editor.marks[0]['points'],[(150,110)])

    def test_click_without_drag_does_not_create_undo_step(self):
        editor=self.make_editor(1)
        editor.press(None,self.event(1,110,90))
        editor.release(None,self.event(1,110,90))
        self.assertEqual(editor.history.past,[])
        self.assertFalse(editor.dirty)

    def test_escape_cancels_drag_without_changing_history(self):
        editor=self.make_editor(1)
        original=deepcopy(editor.marks)
        editor.press(None,self.event(1,110,90))
        editor.motion(None,self.event(1,160,120))
        editor.keypress(None,SimpleNamespace(keyval=Gdk.KEY_Escape))
        self.assertEqual(editor.marks,original)
        self.assertEqual(editor.history.past,[])
        self.assertIsNone(editor.moving)

    def test_css_parses(self):
        Gtk.CssProvider().load_from_data(CSS)

    def test_transparency_affects_margins_only_and_export_has_no_selection(self):
        base=cairo.ImageSurface(cairo.FORMAT_ARGB32,600,400)
        cr=cairo.Context(base)
        cr.set_source_rgb(0,0,1)
        cr.paint()
        editor=SimpleNamespace(base=base, marks=[mark()], scale=1, selected=0,
                   tool='move', current=None, transparent_enabled=True,
                   edit_button=SimpleNamespace(get_active=lambda:True))
        widget=SimpleNamespace(get_allocated_width=lambda:640,get_allocated_height=lambda:440)
        surface=cairo.ImageSurface(cairo.FORMAT_ARGB32,640,440)
        Window.draw(editor,widget,cairo.Context(surface))
        surface.flush()
        self.assertEqual(surface.get_data()[3], 0)
        self.assertEqual(surface.get_data()[30*surface.get_stride()+30*4+3], 255)
        exported=render(base,editor.marks)
        # Compare the capture region: preview has selection, output does not.
        region=cairo.ImageSurface(cairo.FORMAT_ARGB32,600,400)
        rc=cairo.Context(region)
        rc.set_source_surface(surface,-20,-20)
        rc.paint()
        self.assertNotEqual(bytes(region.get_data()),bytes(exported.get_data()))
        self.assertTrue(all(exported.get_data()[i]==255 for i in range(3,len(exported.get_data()),4)))
        editor.transparent_enabled=False
        Window.draw(editor,widget,cairo.Context(surface))
        surface.flush()
        self.assertEqual(surface.get_data()[3],255)

if __name__=='__main__':
    unittest.main()

class ShapeAndStyleTests(unittest.TestCase):
    make_editor = EditingTests.make_editor
    event = EditingTests.event
    def test_shape_movement_resize_crossing_and_undo_at_zoom(self):
        from editing import bounds
        for kind in ('rect', 'ellipse'):
            for scale in (.2, 1, 4):
                editor = self.make_editor(scale)
                editor.marks = [dict(kind=kind, points=[(80,60),(200,160)], width=4, color=(1,0,0,1))]
                original = deepcopy(editor.marks)
                editor.press(None,self.event(scale,140,110))
                editor.release(None,self.event(scale,160,130))
                self.assertEqual(bounds(editor.marks[0]), (100,80,120,100))
                editor.press(None,self.event(scale,220,180))
                editor.release(None,self.event(scale,70,40))
                self.assertEqual(bounds(editor.marks[0]), (70,40,30,40))
                editor.undo()
                self.assertEqual(bounds(editor.marks[0]), (100,80,120,100))
                editor.undo()
                self.assertEqual(editor.marks,original)

    def test_selected_text_color_and_size_export_and_undo(self):
        editor = self.make_editor(.5)
        editor.selected = 0
        editor.syncing_style = False
        before = deepcopy(editor.marks)
        Window.change_style(editor, SimpleNamespace(get_value=lambda:40), 'size')
        self.assertEqual(editor.marks[0]['size'],80)
        Window.change_style(editor, SimpleNamespace(get_rgba=lambda: Gdk.RGBA(0,1,0,1)), 'color')
        self.assertEqual(editor.marks[0]['color'],(0,1,0,1))
        surface = render(editor.base,editor.marks)
        self.assertNotEqual(bytes(surface.get_data()), bytes(render(editor.base,before).get_data()))
        editor.undo()
        self.assertEqual(editor.marks[0]['color'],(1,0,0,1))
        editor.undo()
        self.assertEqual(editor.marks,before)

    def test_sync_does_not_edit_and_size_ignores_shapes(self):
        editor = self.make_editor(1)
        editor.selected = 0
        editor.syncing_style = True
        Window.change_style(editor, SimpleNamespace(get_value=lambda:60), 'size')
        self.assertEqual(editor.history.past,[])
        editor.syncing_style = False
        editor.marks[0]['kind'] = 'rect'
        Window.change_style(editor, SimpleNamespace(get_value=lambda:60), 'size')
        self.assertEqual(editor.history.past,[])

    def test_resize_is_clamped_and_nondegenerate(self):
        from editing import resize, bounds
        original = dict(kind='ellipse',points=[(20,20),(100,100)])
        self.assertEqual(bounds(resize(original,2,(999,999),600,400)),(20,20,579,379))
        x,y,w,h = bounds(resize(original,2,(20,20),600,400))
        self.assertEqual((w,h),(1,1))
