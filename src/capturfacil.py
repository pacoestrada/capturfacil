#!/usr/bin/python3
"""CapturFácil — simple screenshot annotations for GNOME."""
import datetime
from copy import deepcopy
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, Gio, GLib, Gtk
import cairo
from drawing import draw_mark, render
from view import fit_scale, monitor_crop
from editing import History, hit_text, bounds, move_text, hit_mark, handles, hit_handle, resize
import shortcuts

VERSION = '0.1.4'

CSS = b'''
window { background: #f5f7fb; }
window.capturfacil-window.transparent { background-color: transparent; background-image: none; }
window.capturfacil-window .capture-viewport,
window.capturfacil-window .capture-scroll { background-color: transparent; background-image: none; }
.welcome-card { background: #f5f7fb; padding: 24px; border-radius: 16px; }
.viewbar { background: #f5f7fb; color: #34495e; padding: 8px; }
headerbar { background: #ffffff; }
.title { font-size: 27px; font-weight: bold; color: #182f46; }
.subtitle { color: #586b7f; font-size: 14px; }
.capture-choice { padding: 18px 25px; font-size: 17px; border-radius: 12px; }
.sidebar { background: #ffffff; padding: 18px; border-left: 1px solid #dde4ed; }
.sidebar button { padding: 8px 12px; border-radius: 7px; }
.sidebar button:checked { background: #d9eef5; color: #123f52; }
.status { padding: 10px 16px; color: #34495e; background: #eaf0f6; }
.suggested-action { background: #147c87; color: white; }
.small { font-size: 12px; color: #66788b; }
'''


def button(label, callback, style=None):
    obj = Gtk.Button.new_with_label(label)
    obj.connect('clicked', callback)
    if style:
        obj.get_style_context().add_class(style)
    return obj


class Window(Gtk.ApplicationWindow):
    def __init__(self, app, visible=True):
        super().__init__(application=app, title='CapturFácil')
        self.get_style_context().add_class('capturfacil-window')
        self.set_app_paintable(True)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        self.rgba_available = visual is not None
        if visual:
            self.set_visual(visual)
        self.transparent_enabled = False
        self.update_transparency(screen)
        screen.connect('composited-changed', self.update_transparency)
        self.connect('draw', self.clear_background)
        self.set_default_size(1100, 730)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name('capturfacil')
        self.base = None
        self.marks = []
        self.history = History()
        self.selected = None
        self.moving = None
        self.current = None
        self.tool = 'arrow'
        self.zoom = None
        self.full = False
        self.pan = None
        self.capture_monitor = None
        self.scale = 1
        self.offset = (0, 0)
        self.saved = None
        self.dirty = False
        self.process = None
        self.tempdir = None
        self.connect('delete-event', self.close_request)
        self.connect('key-press-event', self.keypress)

        header = Gtk.HeaderBar(title='CapturFácil', subtitle='Captura · señala · guarda')
        header.set_show_close_button(True)
        header.set_decoration_layout(':minimize,maximize,close')
        self.set_resizable(True)
        self.set_titlebar(header)
        self.new_button = button('Nueva captura', self.new_capture)
        header.pack_start(self.new_button)
        self.edit_button = Gtk.ToggleButton(label='✎  Retoques')
        self.edit_button.connect('toggled', self.toggle_editor)
        header.pack_start(self.edit_button)
        self.save_button = button('✓  Listo · guardar', self.finish, 'suggested-action')
        header.pack_end(self.save_button)
        self.copy_button = button('Copiar', self.copy)
        self.copy_button.set_tooltip_text('Copiar la imagen con las anotaciones (Ctrl+C)')
        header.pack_end(self.copy_button)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)
        self.stack = Gtk.Stack()
        root.pack_start(self.stack, True, True, 0)
        welcome = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        welcome.set_valign(Gtk.Align.CENTER)
        welcome.set_halign(Gtk.Align.CENTER)
        welcome.set_border_width(25)
        welcome.get_style_context().add_class('welcome-card')
        title = Gtk.Label(label='¿Qué quieres capturar?')
        title.get_style_context().add_class('title')
        welcome.pack_start(title, False, False, 0)
        subtitle = Gtk.Label(label='Elige una captura y añade solo los retoques que necesites.')
        subtitle.get_style_context().add_class('subtitle')
        welcome.pack_start(subtitle, False, False, 0)
        choices = Gtk.Grid(column_spacing=14, row_spacing=14, column_homogeneous=True)
        for index, (label, mode) in enumerate([('▣  Pantalla actual', 'monitor'), ('▣▣  Todas las pantallas', 'screen'), ('▤  Ventana', 'window'), ('⌗  Área', 'area')]):
            choice = button(label, lambda _b, m=mode: self.capture(m), 'capture-choice')
            choices.attach(choice, index % 2, index // 2, 1, 1)
        welcome.pack_start(choices, False, False, 5)
        hint = Gtk.Label(label='Ventana: tendrás 3 segundos para hacer clic en la ventana que quieras.\nÁrea: arrastra para seleccionar; pulsa Esc para cancelar.')
        hint.set_justify(Gtk.Justification.CENTER)
        hint.get_style_context().add_class('small')
        welcome.pack_start(hint, False, False, 0)
        self.shortcut_button = button('', self.toggle_shortcut)
        self.shortcut_button.set_halign(Gtk.Align.CENTER)
        welcome.pack_start(self.shortcut_button, False, False, 10)
        self.update_shortcut()
        self.stack.add_named(welcome, 'welcome')

        editor_page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        viewbar = Gtk.Box(spacing=8)
        viewbar.get_style_context().add_class('viewbar')
        viewbar.pack_start(button('−', lambda _b: self.change_zoom(1 / 1.25)), False, False, 0)
        self.zoom_label = Gtk.Label(label='Ajustar')
        self.zoom_label.set_width_chars(8)
        viewbar.pack_start(self.zoom_label, False, False, 0)
        viewbar.pack_start(button('+', lambda _b: self.change_zoom(1.25)), False, False, 0)
        viewbar.pack_start(button('Ajustar', lambda _b: self.set_zoom(None)), False, False, 0)
        viewbar.pack_start(button('100 %', lambda _b: self.set_zoom(1.0)), False, False, 0)
        viewbar.pack_start(Gtk.Label(label='Ctrl + rueda: zoom · Botón central: mover'), True, True, 0)
        viewbar.pack_end(button('Pantalla completa · F11', self.toggle_fullscreen), False, False, 0)
        editor_page.pack_start(viewbar, False, False, 0)
        editor = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        editor_page.pack_start(editor, True, True, 0)
        self.scroller = Gtk.ScrolledWindow()
        self.scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.scroller.get_style_context().add_class('capture-scroll')
        self.scroller.set_hexpand(True)
        self.scroller.set_vexpand(True)
        self.viewport = Gtk.Viewport()
        self.viewport.set_shadow_type(Gtk.ShadowType.NONE)
        self.viewport.get_style_context().add_class('capture-viewport')
        self.scroller.add(self.viewport)
        self.viewport.connect('size-allocate', lambda *_args: self.update_view())
        self.canvas = Gtk.DrawingArea()
        self.canvas.set_size_request(320, 220)
        self.canvas.set_can_focus(True)
        self.canvas.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.SMOOTH_SCROLL_MASK)
        self.canvas.connect('draw', self.draw)
        self.canvas.connect('button-press-event', self.press)
        self.canvas.connect('motion-notify-event', self.motion)
        self.canvas.connect('button-release-event', self.release)
        self.canvas.connect('scroll-event', self.scroll_zoom)
        self.viewport.add(self.canvas)
        editor.pack_start(self.scroller, True, True, 0)
        self.revealer = Gtk.Revealer()
        self.revealer.set_transition_type(Gtk.RevealerTransitionType.NONE)
        editor.pack_end(self.revealer, False, False, 0)
        self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
        self.sidebar.get_style_context().add_class('sidebar')
        self.sidebar.set_size_request(205, -1)
        side_scroll = Gtk.ScrolledWindow()
        side_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        side_scroll.set_min_content_width(225)
        side_scroll.add(self.sidebar)
        self.revealer.add(side_scroll)
        group = None
        for label, kind in [('↗  Flecha', 'arrow'), ('╱  Línea', 'line'), ('┄  Línea de puntos', 'dots'), ('○  Círculo / óvalo', 'ellipse'), ('□  Rectángulo', 'rect'), ('T  Texto', 'text'), ('↔  Seleccionar / mover', 'move'), ('✎  Mano alzada', 'pen')]:
            toggle = Gtk.RadioButton.new_with_label_from_widget(group, label)
            toggle.set_mode(False)
            if group is None:
                group = toggle
            toggle.connect('toggled', self.select_tool, kind)
            self.sidebar.pack_start(toggle, False, False, 0)
        controls = Gtk.Box(spacing=10)
        controls.pack_start(Gtk.Label(label='Color'), False, False, 0)
        self.color = Gtk.ColorButton()
        rgba = Gdk.RGBA()
        rgba.parse('#e3424c')
        self.color.set_rgba(rgba)
        self.color.set_title('Color de las anotaciones')
        controls.pack_end(self.color, False, False, 0)
        self.sidebar.pack_start(controls, False, False, 7)
        self.width = self.spin_row('Grosor', 1, 20, 4)
        self.text_size = self.spin_row('Texto', 1, 1000, 28)
        self.syncing_style = False
        self.color.connect('color-set', self.change_style, 'color')
        self.width.connect('value-changed', self.change_style, 'width')
        self.text_size.connect('value-changed', self.change_style, 'size')
        self.sidebar.pack_start(Gtk.Separator(), False, False, 8)
        self.undo_button = button('↶  Deshacer', self.undo)
        self.redo_button = button('↷  Rehacer', self.redo)
        self.sidebar.pack_start(self.undo_button, False, False, 0)
        self.sidebar.pack_start(self.redo_button, False, False, 0)
        tip = Gtk.Label(label='Ctrl+Z  Deshacer\nCtrl+Y  Rehacer\nCtrl+S  Guardar\nCtrl+C  Copiar')
        tip.set_xalign(0)
        tip.get_style_context().add_class('small')
        self.sidebar.pack_end(tip, False, False, 8)
        self.stack.add_named(editor_page, 'editor')
        footer = Gtk.Box(spacing=10)
        footer.get_style_context().add_class('status')
        self.status = Gtk.Label(label='Las capturas se guardarán en Imágenes/Capturas de pantalla.')
        self.status.set_xalign(0)
        self.status.set_line_wrap(True)
        footer.pack_start(self.status, True, True, 0)
        footer.pack_end(button('Abrir carpeta', self.open_folder), False, False, 0)
        root.pack_end(footer, False, False, 0)
        self.update_buttons()
        root.show_all()
        header.show_all()
        self.maximize()
        if visible:
            self.show()

    def update_transparency(self, screen):
        self.transparent_enabled = self.rgba_available and screen.is_composited()
        style = self.get_style_context()
        if self.transparent_enabled:
            style.add_class('transparent')
        else:
            style.remove_class('transparent')
        self.queue_draw()

    def clear_background(self, _widget, cr):
        cr.save()
        cr.set_operator(cairo.OPERATOR_SOURCE)
        if self.transparent_enabled:
            cr.set_source_rgba(0, 0, 0, 0)
        else:
            cr.set_source_rgb(.96, .97, .98)
        cr.paint()
        cr.restore()
        return False

    def toggle_fullscreen(self, _button=None):
        self.full = not self.full
        self.fullscreen() if self.full else self.unfullscreen()

    def update_view(self):
        if self.base is None:
            return
        vw, vh = self.viewport.get_allocated_width(), self.viewport.get_allocated_height()
        if vw < 50 or vh < 50:
            return
        self.scale = self.zoom if self.zoom is not None else fit_scale(
            self.base.get_width(), self.base.get_height(), vw, vh)
        width = max(1, math.ceil(self.base.get_width() * self.scale + 36))
        height = max(1, math.ceil(self.base.get_height() * self.scale + 36))
        if tuple(self.canvas.get_size_request()) != (width, height):
            self.canvas.set_size_request(width, height)
        self.zoom_label.set_text(f'{self.scale * 100:.0f} %')
        self.canvas.queue_draw()

    def set_zoom(self, value):
        if self.base is None:
            return
        old_scale = self.scale
        hadj, vadj = self.scroller.get_hadjustment(), self.scroller.get_vadjustment()
        center = ((hadj.get_value() + hadj.get_page_size()/2 - self.offset[0]) / old_scale,
                  (vadj.get_value() + vadj.get_page_size()/2 - self.offset[1]) / old_scale)
        self.zoom = None if value is None else max(0.05, min(value, 4.0))
        self.update_view()
        def position():
            if self.base is None:
                return False
            for adj, coord, size in [(hadj, center[0], self.base.get_width()),
                                     (vadj, center[1], self.base.get_height())]:
                offset = max(18, (adj.get_page_size() - size * self.scale) / 2)
                adj.set_value(max(0, min(coord * self.scale + offset - adj.get_page_size()/2,
                                        adj.get_upper() - adj.get_page_size())))
            return False
        GLib.timeout_add(40, position)

    def change_zoom(self, factor):
        self.set_zoom(self.scale * factor)

    def scroll_zoom(self, _widget, event):
        if not event.state & Gdk.ModifierType.CONTROL_MASK:
            return False
        if event.direction == Gdk.ScrollDirection.SMOOTH:
            ok, _dx, dy = event.get_scroll_deltas()
            if ok and dy:
                self.change_zoom(1.15 if dy < 0 else 1 / 1.15)
        else:
            self.change_zoom(1.25 if event.direction == Gdk.ScrollDirection.UP else 1 / 1.25)
        return True

    def reset_capture(self):
        self.base = None
        self.marks = []
        self.history = History()
        self.selected = None
        self.moving = None
        self.current = None
        self.pan = None
        self.saved = None
        self.dirty = False
        self.zoom = None
        self.canvas.set_size_request(320, 220)
        self.edit_button.set_active(False)
        self.stack.set_visible_child_name('welcome')
        self.update_buttons()

    def finish(self, _button=None):
        if self.save():
            self.hide()
            self.reset_capture()
            self.set_status('Captura guardada. Elige qué quieres capturar ahora.')
            return True
        return False

    def spin_row(self, label, low, high, default):
        row = Gtk.Box(spacing=10)
        row.pack_start(Gtk.Label(label=label), False, False, 0)
        spin = Gtk.SpinButton.new_with_range(low, high, 1)
        spin.set_value(default)
        row.pack_end(spin, False, False, 0)
        self.sidebar.pack_start(row, False, False, 0)
        return spin

    def set_status(self, message):
        self.status.set_text(message)

    def update_buttons(self):
        ready = self.base is not None and self.stack.get_visible_child_name() == 'editor'
        for control in [self.save_button, self.copy_button, self.edit_button]:
            control.set_sensitive(ready)
        self.undo_button.set_sensitive(bool(self.history.past))
        self.redo_button.set_sensitive(bool(self.history.future))

    def update_shortcut(self):
        self.shortcut_button.set_label('Devolver Impr Pant a GNOME' if shortcuts.active() else 'Usar CapturFácil con Impr Pant')

    def toggle_shortcut(self, _button):
        try:
            if shortcuts.active():
                shortcuts.restore()
                self.set_status('Se ha devuelto Impr Pant a su configuración anterior.')
            else:
                if not Path('/usr/bin/capturfacil').exists():
                    raise RuntimeError('Instala primero el paquete .deb para activar Impr Pant.')
                shortcuts.install()
                self.set_status('Impr Pant ya abre CapturFácil. Al desinstalar se recuperará su configuración anterior.')
        except Exception as exc:
            self.error(str(exc))
        self.update_shortcut()

    def toggle_editor(self, toggle):
        self.revealer.set_reveal_child(toggle.get_active())
        self.canvas.queue_draw()
        if toggle.get_active():
            self.set_status('Seleccionar / mover: arrastra texto o formas; ajusta las formas desde sus esquinas. Color y Texto cambian la selección.')
        self.canvas.grab_focus()

    def select_tool(self, widget, kind):
        if widget.get_active():
            self.tool = kind
            self.selected = None
            if hasattr(self, 'canvas'):
                self.canvas.queue_draw()

    def discard_ok(self):
        if not self.dirty:
            return True
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
                                   text='La captura todavía no está guardada.')
        dialog.format_secondary_text('Puedes guardarla antes de continuar.')
        dialog.add_buttons('Cancelar', Gtk.ResponseType.CANCEL, 'Descartar', Gtk.ResponseType.REJECT, 'Guardar', Gtk.ResponseType.ACCEPT)
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.ACCEPT:
            return self.save(None)
        return response == Gtk.ResponseType.REJECT

    def new_capture(self, _button):
        if self.discard_ok():
            self.reset_capture()
            self.set_status('Elige pantalla actual, todas las pantallas, ventana o área.')

    def capture(self, mode):
        if self.tempdir is not None:
            return
        self.capture_monitor = None
        if mode == 'monitor':
            display = self.get_display()
            monitor = display.get_monitor_at_window(self.get_window())
            geo = monitor.get_geometry()
            rects = [display.get_monitor(i).get_geometry() for i in range(display.get_n_monitors())]
            left, top = min(r.x for r in rects), min(r.y for r in rects)
            right, bottom = max(r.x + r.width for r in rects), max(r.y + r.height for r in rects)
            self.capture_monitor = ((geo.x, geo.y, geo.width, geo.height),
                                    (left, top, right-left, bottom-top))
        self.hide()
        self.tempdir = tempfile.TemporaryDirectory(prefix='capturfacil-')
        self.capture_path = Path(self.tempdir.name) / 'capture.png'
        def start():
            args = ['gnome-screenshot', '-f', str(self.capture_path)]
            if mode == 'area':
                args.append('-a')
            elif mode == 'window':
                args.extend(['-w', '-d', '3'])
            try:
                self.process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                self.started = time.monotonic()
                GLib.timeout_add(100, self.check_capture)
            except OSError as exc:
                self.cleanup_capture()
                self.present()
                self.error(f'No se pudo iniciar la captura: {exc}')
            return False
        GLib.timeout_add(400, start)

    def check_capture(self):
        if self.process.poll() is None:
            if time.monotonic() - self.started < 120:
                return True
            self.process.terminate()
            try:
                self.process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.communicate()
            self.cleanup_capture()
            self.present()
            self.set_status('Captura cancelada por tiempo de espera. Puedes intentarlo de nuevo.')
            return False
        _, stderr = self.process.communicate()
        code = self.process.returncode
        try:
            if self.capture_path.exists() and self.capture_path.stat().st_size:
                self.load_image(str(self.capture_path), self.capture_monitor)
            elif code and stderr:
                self.error('No se pudo obtener la captura. ' + stderr.decode(errors='replace')[-400:])
            else:
                self.set_status('Captura cancelada. Puedes volver a seleccionar un área.')
        except Exception as exc:
            self.error(f'No se pudo abrir la captura: {exc}')
        finally:
            self.cleanup_capture()
            self.present()
        return False

    def cleanup_capture(self):
        self.process = None
        if self.tempdir:
            self.tempdir.cleanup()
            self.tempdir = None

    def load_image(self, path, monitor=None):
        self.base = cairo.ImageSurface.create_from_png(path)
        if monitor:
            self.base = monitor_crop(self.base, *monitor)
        self.zoom = None
        self.marks = []
        self.history = History()
        self.selected = None
        self.moving = None
        self.current = None
        self.saved = None
        self.dirty = True
        self.stack.set_visible_child_name('editor')
        self.edit_button.set_active(False)
        self.update_buttons()
        self.set_status(f'{self.base.get_width()} × {self.base.get_height()} px · Pulsa Retoques para anotar o Listo para guardar.')
        self.maximize()
        self.update_view()
        GLib.idle_add(lambda: (self.update_view(), False)[1])
        self.canvas.queue_draw()

    def draw(self, widget, cr):
        cr.save()
        cr.set_operator(cairo.OPERATOR_SOURCE)
        if self.transparent_enabled:
            cr.set_source_rgba(0, 0, 0, 0)
        else:
            cr.set_source_rgb(.87, .9, .94)
        cr.paint()
        cr.restore()
        if self.base is None:
            return
        width, height = widget.get_allocated_width(), widget.get_allocated_height()
        self.offset = ((width - self.base.get_width() * self.scale) / 2, (height - self.base.get_height() * self.scale) / 2)
        cr.translate(*self.offset)
        cr.scale(self.scale, self.scale)
        cr.rectangle(0, 0, self.base.get_width(), self.base.get_height())
        cr.clip()
        cr.set_source_surface(self.base, 0, 0)
        cr.paint()
        for mark in self.marks:
            draw_mark(cr, mark)
        if self.current:
            draw_mark(cr, self.current)
        if self.selected is not None and self.edit_button.get_active() and self.tool in ('text', 'move'):
            x, y, width, height = bounds(self.marks[self.selected])
            padding = 4 / self.scale
            cr.set_line_width(1.5 / self.scale)
            cr.set_dash([5 / self.scale, 4 / self.scale])
            cr.set_source_rgb(.05, .55, .7)
            cr.rectangle(x-padding, y-padding, width+2*padding, height+2*padding)
            cr.stroke()
            cr.set_dash([])
            for hx, hy in handles(self.marks[self.selected]):
                radius = 4 / self.scale
                cr.rectangle(hx-radius, hy-radius, 2*radius, 2*radius)
                cr.fill()

    def sync_style(self):
        if self.selected is None:
            return
        mark = self.marks[self.selected]
        self.syncing_style = True
        try:
            self.color.set_rgba(Gdk.RGBA(*mark['color']))
            self.width.set_value(mark['width'] * self.scale)
            if mark['kind'] == 'text':
                self.text_size.set_value(mark['size'] * self.scale)
        finally:
            self.syncing_style = False

    def change_style(self, widget, field):
        if self.syncing_style or self.selected is None or self.moving:
            return
        mark = self.marks[self.selected]
        if field == 'size' and mark['kind'] != 'text':
            return
        if field == 'color':
            color = widget.get_rgba()
            value = (color.red, color.green, color.blue, 1)
        else:
            value = widget.get_value() / self.scale
        if mark.get(field) != value:
            self.history.record(self.marks)
            mark[field] = value
            self.changed()

    def point(self, event, clamp=False):
        x = (event.x - self.offset[0]) / self.scale
        y = (event.y - self.offset[1]) / self.scale
        if clamp:
            return (min(max(x, 0), self.base.get_width() - 1), min(max(y, 0), self.base.get_height() - 1))
        if 0 <= x < self.base.get_width() and 0 <= y < self.base.get_height():
            return (x, y)
        return None

    def press(self, _widget, event):
        if event.button == 2:
            self.pan = (event.x_root, event.y_root,
                        self.scroller.get_hadjustment().get_value(),
                        self.scroller.get_vadjustment().get_value())
            return True
        if event.button != 1 or not self.base or not self.edit_button.get_active():
            return False
        point = self.point(event)
        if point is None:
            return False
        self.canvas.grab_focus()
        if self.tool in ('text', 'move'):
            corner = None
            if self.tool == 'move' and self.selected is not None:
                corner = hit_handle(self.marks[self.selected], point, 7 / self.scale)
            if corner is None:
                hit = hit_mark if self.tool == 'move' else hit_text
                self.selected = hit(self.marks, point, 5 / self.scale)
            if self.selected is not None:
                self.sync_style()
                self.moving = {'start': point, 'before': deepcopy(self.marks), 'index': self.selected, 'corner': corner}
                self.canvas.queue_draw()
                return True
            if self.tool == 'move':
                self.set_status('Arrastra texto, rectángulos u óvalos. Selecciona una forma y arrastra sus esquinas para ajustarla.')
                self.canvas.queue_draw()
                return True
        color = self.color.get_rgba()
        mark = {'kind': self.tool, 'points': [point], 'width': self.width.get_value() / self.scale,
                'color': (color.red, color.green, color.blue, 1)}
        if self.tool == 'text':
            text = self.ask_text()
            if text:
                mark.update(text=text, size=self.text_size.get_value() / self.scale)
                self.add_mark(mark)
        else:
            self.current = mark
        self.canvas.queue_draw()
        return True

    def motion(self, _widget, event):
        if self.pan:
            x, y, hx, vy = self.pan
            self.scroller.get_hadjustment().set_value(hx + x - event.x_root)
            self.scroller.get_vadjustment().set_value(vy + y - event.y_root)
            return True
        if self.moving:
            point = self.point(event, True)
            start = self.moving['start']
            index = self.moving['index']
            original = self.moving['before'][index]
            if self.moving.get('corner') is not None:
                self.marks[index] = resize(original, self.moving['corner'], point,
                                          self.base.get_width(), self.base.get_height())
            else:
                self.marks[index] = move_text(original, point[0]-start[0], point[1]-start[1],
                                             self.base.get_width(), self.base.get_height())
            self.canvas.queue_draw()
            return True
        if self.current:
            point = self.point(event, True)
            if self.tool == 'pen':
                self.current['points'].append(point)
            else:
                self.current['points'] = [self.current['points'][0], point]
            self.canvas.queue_draw()
        return True

    def release(self, _widget, event):
        if event.button == 2:
            self.pan = None
            return True
        if event.button == 1 and self.moving:
            self.motion(_widget, event)
            if self.marks != self.moving['before']:
                self.history.record(self.moving['before'])
                self.changed()
            self.moving = None
            return True
        if event.button == 1 and self.current:
            self.motion(_widget, event)
            mark = self.current
            self.current = None
            if mark['kind'] == 'pen' or math.dist(mark['points'][0], mark['points'][-1]) > 1:
                self.add_mark(mark)
        return True

    def ask_text(self):
        dialog = Gtk.Dialog(title='Añadir texto', transient_for=self, modal=True)
        dialog.add_buttons('Cancelar', Gtk.ResponseType.CANCEL, 'Añadir', Gtk.ResponseType.OK)
        dialog.set_default_size(400, 190)
        box = dialog.get_content_area()
        box.set_border_width(16)
        box.set_spacing(8)
        box.pack_start(Gtk.Label(label='Escribe el texto de la anotación', xalign=0), False, False, 0)
        view = Gtk.TextView()
        view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(85)
        scroll.add(view)
        box.pack_start(scroll, True, True, 0)
        dialog.show_all()
        view.grab_focus()
        result = dialog.run()
        buffer = view.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False).strip()
        dialog.destroy()
        return text if result == Gtk.ResponseType.OK else ''

    def add_mark(self, mark):
        self.history.record(self.marks)
        self.marks.append(mark)
        self.selected = len(self.marks)-1 if mark['kind'] == 'text' else None
        self.changed()

    def changed(self):
        self.dirty = True
        self.update_buttons()
        self.canvas.queue_draw()

    def undo(self, _button=None):
        if self.history.past:
            self.marks = self.history.undo(self.marks)
            self.selected = None
            self.changed()

    def redo(self, _button=None):
        if self.history.future:
            self.marks = self.history.redo(self.marks)
            self.selected = None
            self.changed()

    def folder(self):
        pictures = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES)
        return Path(pictures or Path.home() / 'Imágenes') / 'Capturas de pantalla'

    def save(self, _button=None):
        if self.base is None:
            return False
        try:
            if self.dirty or self.saved is None or not self.saved.exists():
                folder = self.folder()
                folder.mkdir(parents=True, exist_ok=True)
                stamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')
                path = folder / f'Captura_{stamp}.png'
                # Exclusive creation prevents replacing an unrelated file.
                created = False
                try:
                    with path.open('xb') as stream:
                        created = True
                        render(self.base, self.marks).write_to_png(stream)
                except Exception:
                    if created:
                        path.unlink(missing_ok=True)
                    raise
                self.saved = path
                self.dirty = False
            self.set_status(f'Guardada · {self.saved.name}')
            return True
        except Exception as exc:
            self.error(f'No se pudo guardar la captura. Tus anotaciones siguen abiertas.\n{exc}')
            return False

    def copy(self, _button=None):
        if self.base is None:
            return
        try:
            surface = render(self.base, self.marks)
            pixbuf = Gdk.pixbuf_get_from_surface(surface, 0, 0, surface.get_width(), surface.get_height())
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_image(pixbuf)
            clipboard.set_can_store(None)
            clipboard.store()
            self.set_status('Imagen con anotaciones copiada. Puedes pegarla con Ctrl+V. Pulsa Listo para guardarla también.')
        except Exception as exc:
            self.error(f'No se pudo copiar la imagen: {exc}')

    def open_folder(self, _button=None):
        try:
            self.folder().mkdir(parents=True, exist_ok=True)
            Gio.AppInfo.launch_default_for_uri(self.folder().as_uri(), None)
        except Exception as exc:
            self.error(f'No se pudo abrir la carpeta: {exc}')

    def keypress(self, _widget, event):
        if self.moving:
            if event.keyval == Gdk.KEY_Escape:
                self.marks = self.moving['before']
                self.moving = None
                self.canvas.queue_draw()
            return True
        if event.keyval == Gdk.KEY_F11:
            self.toggle_fullscreen()
            return True
        if event.state & Gdk.ModifierType.CONTROL_MASK:
            key = Gdk.keyval_name(event.keyval).lower()
            if key in ['plus', 'equal', 'KP_Add', 'minus', 'KP_Subtract', '0']:
                if key == '0':
                    self.set_zoom(None)
                else:
                    self.change_zoom(1 / 1.25 if key in ['minus', 'KP_Subtract'] else 1.25)
                return True
            actions = {'z': self.undo, 'y': self.redo, 's': self.finish, 'c': self.copy}
            if key == 'z' and event.state & Gdk.ModifierType.SHIFT_MASK:
                self.redo()
                return True
            if key in actions:
                actions[key]()
                return True
        if event.keyval == Gdk.KEY_Escape and self.current:
            self.current = None
            self.canvas.queue_draw()
            return True
        return False

    def close_request(self, _window, _event):
        if self.discard_ok():
            self.hide()
            self.reset_capture()
        return True

    def error(self, message):
        self.present()
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, message_type=Gtk.MessageType.ERROR,
                                   buttons=Gtk.ButtonsType.CLOSE, text='CapturFácil')
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()


class Application(Gtk.Application):
    def __init__(self, background=False):
        super().__init__(application_id='es.compilando.CapturFacil', flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.window = None
        self.background = background

    def do_startup(self):
        Gtk.Application.do_startup(self)
        self.hold()
        css = Gtk.CssProvider()
        css.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        action = Gio.SimpleAction.new('quit', None)
        action.connect('activate', self.quit_requested)
        self.add_action(action)
        # Stop a resident instance after its installed code is upgraded or removed.
        self.code_stamp = Path(__file__).stat().st_mtime_ns
        GLib.timeout_add_seconds(5, self.check_installed_code)

    def check_installed_code(self):
        try:
            changed = Path(__file__).stat().st_mtime_ns != self.code_stamp
        except FileNotFoundError:
            changed = True
        if changed and (self.window is None or
                        (not self.window.get_visible() and self.window.tempdir is None)):
            if Path(__file__).exists() and shortcuts.active():
                os.execv(sys.executable, [sys.executable, __file__, '--background'])
            self.quit()
            return False
        return True

    def quit_requested(self, *_args):
        if self.window is None or self.window.discard_ok():
            self.quit()

    def do_activate(self):
        if self.window is None:
            self.window = Window(self, visible=False)
            self.window.connect('destroy', lambda _w: setattr(self, 'window', None))
        if self.background:
            self.background = False
            return
        if self.window.tempdir is None:
            self.window.present()


if __name__ == '__main__':
    if '--version' in sys.argv:
        print('CapturFácil ' + VERSION)
    elif '--quit' in sys.argv:
        app = Application()
        app.register(None)
        if app.get_is_remote():
            app.activate_action('quit', None)
    elif '--background' in sys.argv:
        if shortcuts.active():
            app = Application(background=True)
            app.register(None)
            if not app.get_is_remote():
                sys.exit(app.run([sys.argv[0]]))
    else:
        sys.exit(Application().run(sys.argv))
