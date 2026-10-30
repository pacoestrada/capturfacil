import os
from pathlib import Path
import sys
import tempfile
import unittest
import runpy
from types import SimpleNamespace
from unittest.mock import patch

os.environ['GSETTINGS_BACKEND'] = 'memory'
CONFIG = tempfile.TemporaryDirectory()
os.environ['XDG_CONFIG_HOME'] = CONFIG.name
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import cairo
from gi.repository import Gio
import shortcuts as s
from drawing import render


class ShortcutTests(unittest.TestCase):
    def setUp(self):
        self.media = s.settings(s.SCHEMA)
        self.shell = s.settings('org.gnome.shell.keybindings')
        self.media.set_strv('custom-keybindings', [])
        self.shell.set_strv('show-screenshot-ui', ['Print', '<Shift>Print'])
        for key in ['name', 'command', 'binding']:
            s.settings(s.CUSTOM, s.BINDING).reset(key)
        s.STATE.unlink(missing_ok=True)

    def test_install_restore_preserves_previous_and_other_bindings(self):
        other = '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/other/'
        self.media.set_strv('custom-keybindings', [other])
        s.install()
        self.assertTrue(s.active())
        self.assertEqual(self.shell.get_strv('show-screenshot-ui'), ['<Shift>Print'])
        self.assertTrue(s.RECOVERY.exists())
        self.assertTrue(s.AUTOSTART.exists())
        s.install()  # idempotent; never back up our own modified setting
        s.restore()
        self.assertEqual(self.shell.get_strv('show-screenshot-ui'), ['Print', '<Shift>Print'])
        self.assertEqual(self.media.get_strv('custom-keybindings'), [other])
        self.assertFalse(s.STATE.exists())
        self.assertFalse(s.AUTOSTART.exists())
        self.assertFalse(s.RECOVERY.exists())
        s.restore()

    def test_offline_recovery_helper_restores_next_login(self):
        s.install()
        original_argv = sys.argv
        try:
            sys.argv = [str(s.RECOVERY), '--recover']
            exists = Path.exists
            with patch.object(Path, 'exists', lambda path: False if str(path) == s.COMMAND else exists(path)):
                runpy.run_path(str(s.RECOVERY), run_name='__main__')
        finally:
            sys.argv = original_argv
        self.assertFalse(s.STATE.exists())
        self.assertEqual(self.shell.get_strv('show-screenshot-ui'), ['Print', '<Shift>Print'])

    def test_respects_user_change_to_native_binding(self):
        s.install()
        self.shell.set_strv('show-screenshot-ui', ['<Alt>Print'])
        s.restore()
        self.assertEqual(self.shell.get_strv('show-screenshot-ui'), ['<Alt>Print'])

    def test_respects_reassigned_custom_binding(self):
        s.install()
        s.settings(s.CUSTOM, s.BINDING).set_string('command', '/usr/bin/another-app')
        s.restore()
        self.assertIn(s.BINDING, self.media.get_strv('custom-keybindings'))
        self.assertEqual(self.shell.get_strv('show-screenshot-ui'), ['<Shift>Print'])

    def test_new_print_binding_is_not_overwritten_on_restore(self):
        s.install()
        other = '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/new/'
        s.settings(s.CUSTOM, other).set_string('binding', 'Print')
        self.media.set_strv('custom-keybindings', [s.BINDING, other])
        s.restore()
        self.assertEqual(self.shell.get_strv('show-screenshot-ui'), ['<Shift>Print'])
        self.assertEqual(self.media.get_strv('custom-keybindings'), [other])

    def test_transaction_rolls_back_on_failure(self):
        real_set = s.set_value
        def fail(obj, key, value):
            if key == 'custom-keybindings' and s.BINDING in value:
                raise RuntimeError('simulated write failure')
            return real_set(obj, key, value)
        s.set_value = fail
        try:
            with self.assertRaises(RuntimeError):
                s.install()
        finally:
            s.set_value = real_set
        self.assertEqual(self.shell.get_strv('show-screenshot-ui'), ['Print', '<Shift>Print'])
        self.assertFalse(s.STATE.exists())

    def test_existing_custom_print_is_left_alone(self):
        other = '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/existing/'
        s.settings(s.CUSTOM, other).set_string('binding', 'Print')
        self.media.set_strv('custom-keybindings', [other])
        with self.assertRaises(RuntimeError):
            s.install()
        self.assertFalse(s.STATE.exists())
        self.assertEqual(self.shell.get_strv('show-screenshot-ui'), ['Print', '<Shift>Print'])


class RenderTests(unittest.TestCase):
    def test_all_annotations_export_without_resizing_original(self):
        base = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1200, 700)
        cr = cairo.Context(base)
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
        before = bytes(base.get_data())
        marks = []
        for i, kind in enumerate(['arrow', 'line', 'dots', 'ellipse', 'rect', 'text', 'pen']):
            marks.append({'kind': kind, 'points': [(40 + i * 150, 100), (140 + i * 150, 180)],
                          'width': 5, 'color': (1, 0, 0, 1), 'text': '¡Captura fácil!\nEspaña', 'size': 25})
        result = render(base, marks)
        self.assertEqual((result.get_width(), result.get_height()), (1200, 700))
        self.assertNotEqual(bytes(result.get_data()), before)
        self.assertEqual(bytes(base.get_data()), before)
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / 'test.png')
            result.write_to_png(path)
            loaded = cairo.ImageSurface.create_from_png(path)
            self.assertEqual(loaded.get_width(), 1200)


class SaveTests(unittest.TestCase):
    def test_save_keeps_resolution_and_older_versions(self):
        from capturfacil import Window
        with tempfile.TemporaryDirectory() as tmp:
            base = cairo.ImageSurface(cairo.FORMAT_ARGB32, 800, 450)
            errors = []
            w = SimpleNamespace(base=base, marks=[], saved=None, dirty=True,
                                folder=lambda: Path(tmp), set_status=lambda message: None, error=errors.append)
            self.assertTrue(Window.save(w))
            first = w.saved
            self.assertTrue(Window.save(w))
            self.assertEqual(first, w.saved)
            w.dirty = True
            self.assertTrue(Window.save(w))
            self.assertNotEqual(first, w.saved)
            self.assertTrue(first.exists())
            loaded = cairo.ImageSurface.create_from_png(str(w.saved))
            self.assertEqual((loaded.get_width(), loaded.get_height()), (800, 450))
            self.assertEqual(errors, [])

    def test_failed_export_removes_partial_file_keeps_edits(self):
        from capturfacil import Window
        with tempfile.TemporaryDirectory() as tmp:
            errors = []
            marks = [{'kind': 'text'}]
            w = SimpleNamespace(base=object(), marks=marks, saved=None, dirty=True,
                                folder=lambda: Path(tmp), set_status=lambda message: None, error=errors.append)
            with patch('capturfacil.render', side_effect=OSError('disk error')):
                self.assertFalse(Window.save(w))
            self.assertEqual(list(Path(tmp).iterdir()), [])
            self.assertTrue(w.dirty)
            self.assertIs(w.marks, marks)
            self.assertEqual(len(errors), 1)


if __name__ == '__main__':
    unittest.main()
