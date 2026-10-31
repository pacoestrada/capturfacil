#!/usr/bin/python3
"""User-owned shortcut transaction; also retained for offline uninstall recovery."""
import json
import os
from pathlib import Path
import shutil
import sys
import time
from gi.repository import Gio

SCHEMA = 'org.gnome.settings-daemon.plugins.media-keys'
CUSTOM = SCHEMA + '.custom-keybinding'
BINDING = '/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/capturfacil/'
COMMAND = '/usr/bin/capturfacil'
ROOT = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
STATE = ROOT / 'capturfacil' / 'shortcut.json'
RECOVERY = ROOT / 'capturfacil' / 'recover-shortcut.py'
AUTOSTART = ROOT / 'autostart' / 'capturfacil-recovery.desktop'


def settings(schema, path=None):
    source = Gio.SettingsSchemaSource.get_default()
    found = source.lookup(schema, True)
    if not found:
        raise RuntimeError('Esta integración necesita el escritorio GNOME.')
    return Gio.Settings.new_full(found, None, path)


def read_state():
    return json.loads(STATE.read_text()) if STATE.exists() else None


def write_state(data):
    STATE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = STATE.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2))
    tmp.chmod(0o600)
    tmp.replace(STATE)


def active():
    try:
        return (read_state() is not None and
                BINDING in settings(SCHEMA).get_strv('custom-keybindings') and
                settings(CUSTOM, BINDING).get_string('command') == COMMAND and
                settings(CUSTOM, BINDING).get_string('binding') == 'Print')
    except Exception:
        return False


def set_value(obj, key, value):
    if not obj.is_writable(key):
        raise RuntimeError('El sistema no permite cambiar el atajo de teclado.')
    ok = obj.set_strv(key, value) if isinstance(value, list) else obj.set_string(key, value)
    if not ok:
        raise RuntimeError('No se ha podido guardar el atajo de teclado.')


def install():
    if active():
        return
    if STATE.exists():
        restore()
    media = settings(SCHEMA)
    custom = settings(CUSTOM, BINDING)
    paths = list(media.get_strv('custom-keybindings'))
    if BINDING in paths:
        raise RuntimeError('Ya existe un atajo con este identificador. No se modificará.')
    # Do not take Print from a different custom application.
    for path in paths:
        other = settings(CUSTOM, path)
        if other.get_string('binding') == 'Print':
            raise RuntimeError('Impr Pant ya está asignada a otro atajo personalizado. Puedes abrir CapturFácil desde el menú.')
    changes = []
    for schema, keys in [('org.gnome.shell.keybindings', ['show-screenshot-ui', 'screenshot']),
                         (SCHEMA, ['screenshot'])]:
        try:
            obj = settings(schema)
        except RuntimeError:
            continue
        for key in keys:
            if not obj.props.settings_schema.has_key(key):
                continue
            before = list(obj.get_strv(key))
            after = [x for x in before if x != 'Print']
            if before != after:
                if not obj.is_writable(key):
                    raise RuntimeError('GNOME tiene bloqueado el atajo de captura.')
                changes.append({'schema': schema, 'key': key, 'before': before, 'after': after})
    if not media.is_writable('custom-keybindings') or any(not custom.is_writable(k) for k in ['name', 'command', 'binding']):
        raise RuntimeError('No tienes permiso para modificar los atajos.')
    write_state({'changes': changes})  # durable backup before any settings change
    shutil.copyfile(__file__, RECOVERY)
    AUTOSTART.parent.mkdir(parents=True, exist_ok=True)
    quoted = str(RECOVERY).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%')
    AUTOSTART.write_text('[Desktop Entry]\nType=Application\nName=Recuperación de Impr Pant\n'
                         f'Exec=/usr/bin/python3 "{quoted}" --recover\nNoDisplay=true\nX-GNOME-Autostart-enabled=true\n')
    try:
        set_value(custom, 'name', 'CapturFácil')
        set_value(custom, 'command', COMMAND)
        set_value(custom, 'binding', 'Print')
        for change in changes:
            set_value(settings(change['schema']), change['key'], change['after'])
        set_value(media, 'custom-keybindings', paths + [BINDING])
        Gio.Settings.sync()
    except Exception:
        restore()
        raise


def restore_gnome():
    """Explicit user request to enable GNOME, even with an empty/missing backup.

    Uninstall still uses restore() to preserve the user's previous preferences.
    """
    media = settings(SCHEMA)
    paths = list(media.get_strv('custom-keybindings'))
    for path in paths:
        custom = settings(CUSTOM, path)
        if custom.get_string('binding') == 'Print' and (
                path != BINDING or custom.get_string('command') != COMMAND):
            raise RuntimeError('Impr Pant pertenece a otro atajo personalizado. No se ha modificado.')
    target = None
    for schema, key in [('org.gnome.shell.keybindings', 'show-screenshot-ui'),
                        (SCHEMA, 'screenshot')]:
        try:
            obj = settings(schema)
        except RuntimeError:
            continue
        if obj.props.settings_schema.has_key(key) and obj.is_writable(key):
            target = obj, key
            break
    if target is None:
        raise RuntimeError('No se ha encontrado un atajo de captura de GNOME que se pueda activar.')
    # Release the media-keys grab before GNOME Shell tries to acquire Print.
    custom = settings(CUSTOM, BINDING)
    if custom.get_string('command') == COMMAND and custom.get_string('binding') == 'Print':
        set_value(media, 'custom-keybindings', [p for p in paths if p != BINDING])
        Gio.Settings.sync()
        time.sleep(0.25)
    restore()
    obj, key = target
    current = list(obj.get_strv(key))
    if 'Print' not in current:
        set_value(obj, key, current + ['Print'])
    # Also repair the owned binding when its backup has disappeared.
    custom = settings(CUSTOM, BINDING)
    if custom.get_string('command') == COMMAND and custom.get_string('binding') == 'Print':
        set_value(media, 'custom-keybindings', [p for p in media.get_strv('custom-keybindings') if p != BINDING])
        for name in ['name', 'command', 'binding']:
            custom.reset(name)
    Gio.Settings.sync()
    if 'Print' not in obj.get_strv(key) or active():
        raise RuntimeError('No se ha podido verificar la devolución de Impr Pant a GNOME.')


def restore():
    data = read_state()
    if not data:
        return
    media = settings(SCHEMA)
    custom = settings(CUSTOM, BINDING)
    # Leave a binding that the user subsequently reassigned untouched.
    ours = custom.get_string('command') == COMMAND and custom.get_string('binding') == 'Print'
    paths = list(media.get_strv('custom-keybindings'))
    other_print = any(settings(CUSTOM, p).get_string('binding') == 'Print' for p in paths if p != BINDING)
    changed_custom = BINDING in paths and not ours
    if ours:
        set_value(media, 'custom-keybindings', [p for p in paths if p != BINDING])
        for key in ['name', 'command', 'binding']:
            custom.reset(key)
    for change in data['changes']:
        obj = settings(change['schema'])
        if list(obj.get_strv(change['key'])) == change['after'] and not other_print and not changed_custom:
            set_value(obj, change['key'], change['before'])
    Gio.Settings.sync()
    STATE.unlink(missing_ok=True)
    AUTOSTART.unlink(missing_ok=True)
    RECOVERY.unlink(missing_ok=True)


if __name__ == '__main__':
    try:
        if '--restore' in sys.argv or ('--recover' in sys.argv and not Path(COMMAND).exists()):
            restore()
        elif '--install' in sys.argv:
            install()
    except Exception as exc:
        print(f'CapturFácil: {exc}', file=sys.stderr)
        sys.exit(1)
