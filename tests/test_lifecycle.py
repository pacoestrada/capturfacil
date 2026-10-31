import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
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
        with patch('capturfacil.present_requested', side_effect=lambda window:window.present()) as present:
            Application.do_activate(app)
            present.assert_called_once_with(w)
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

class UpgradeTests(unittest.TestCase):
    def test_hidden_upgrade_restarts_but_visible_work_is_preserved(self):
        from unittest.mock import patch
        for visible in (True, False):
            app = SimpleNamespace(code_stamp=0,
                window=SimpleNamespace(get_visible=lambda:visible,tempdir=None),
                quit=lambda: self.fail('do not discard the resident process before replacement'))
            with patch('capturfacil.shortcuts.active',return_value=True), patch('capturfacil.os.execv') as restart:
                if visible:
                    self.assertTrue(Application.check_installed_code(app))
                    restart.assert_not_called()
                else:
                    restart.side_effect=RuntimeError('replacement process')
                    with self.assertRaisesRegex(RuntimeError,'replacement process'):
                        Application.check_installed_code(app)
                    self.assertEqual(restart.call_args.args[1][-1],'--background')
