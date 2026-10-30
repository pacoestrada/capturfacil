import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from capturfacil import Window, Application


class LifecycleTests(unittest.TestCase):
    def test_finish_saves_before_hiding_and_resetting(self):
        calls = []
        w = SimpleNamespace(save=lambda: (calls.append('save'), True)[1],
                            hide=lambda: calls.append('hide'),
                            reset_capture=lambda: calls.append('reset'),
                            set_status=lambda _: calls.append('status'))
        self.assertTrue(Window.finish(w))
        self.assertEqual(calls, ['save', 'hide', 'reset', 'status'])

    def test_failed_save_keeps_window_and_edits(self):
        w = SimpleNamespace(save=lambda: False,
                            hide=lambda: self.fail('must stay visible'),
                            reset_capture=lambda: self.fail('must retain edits'))
        self.assertFalse(Window.finish(w))

    def test_warm_activation_reuses_window(self):
        calls = []
        w = SimpleNamespace(tempdir=None, present=lambda: calls.append('present'))
        app = SimpleNamespace(window=w, background=False)
        Application.do_activate(app)
        self.assertIs(app.window, w)
        self.assertEqual(calls, ['present'])

    def test_background_activation_does_not_show_window(self):
        w = SimpleNamespace(tempdir=None, present=lambda: self.fail('must remain hidden'))
        app = SimpleNamespace(window=w, background=True)
        Application.do_activate(app)
        self.assertFalse(app.background)

    def test_activation_during_capture_does_not_contaminate_screenshot(self):
        w = SimpleNamespace(tempdir=object(), present=lambda: self.fail('must remain hidden'))
        Application.do_activate(SimpleNamespace(window=w, background=False))

if __name__ == '__main__':
    unittest.main()
