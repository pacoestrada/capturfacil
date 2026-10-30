#!/usr/bin/python3
"""Build the self-contained, architecture-independent Debian package."""
from pathlib import Path
import shutil
import subprocess
import tarfile

BASE = Path(__file__).resolve().parent
ROOT = BASE / 'build' / 'capturfacil'
if ROOT.exists():
    shutil.rmtree(ROOT)

def write(path, contents, mode=0o644):
    dest = ROOT / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(contents)
    dest.chmod(mode)

write('DEBIAN/control', '''Package: capturfacil
Version: 0.1.2
Section: graphics
Priority: optional
Architecture: all
Maintainer: CapturFacil <capturfacil@localhost>
Depends: python3, python3-gi, python3-gi-cairo, python3-cairo, gir1.2-gtk-3.0, gir1.2-pango-1.0, gnome-screenshot, util-linux, libglib2.0-bin
Recommends: gnome-shell
Description: Capturas de pantalla y anotaciones sencillas para GNOME
 Captura pantalla, ventana o area y anade flechas, texto, formas
 y dibujo a mano alzada. Guarda PNG automaticamente en Imagenes. Incluye gestion reversible del atajo Impr Pant.
''')
write('usr/bin/capturfacil', '''#!/bin/sh
if [ "$#" -eq 0 ]; then
  if /usr/bin/gdbus call --session --dest es.compilando.CapturFacil \\
       --object-path /es/compilando/CapturFacil \\
       --method org.freedesktop.Application.Activate '{}' --timeout 1 >/dev/null 2>&1; then
    exit 0
  fi
fi
exec /usr/bin/python3 /usr/share/capturfacil/capturfacil.py "$@"
''', 0o755)
for src in (BASE / 'src').glob('*.py'):
    write('usr/share/capturfacil/' + src.name, src.read_text())
write('usr/share/applications/capturfacil.desktop', '''[Desktop Entry]
Type=Application
Name=CapturFácil
GenericName=Capturas de pantalla
Comment=Captura, añade anotaciones y guarda sin complicaciones
Exec=capturfacil
Icon=capturfacil
Terminal=false
Categories=Graphics;GTK;
Keywords=captura;pantalla;flecha;anotar;screenshot;
StartupNotify=true
StartupWMClass=capturfacil.py
''')
write('etc/xdg/autostart/capturfacil.desktop', """[Desktop Entry]
Type=Application
Name=CapturFácil en segundo plano
Exec=capturfacil --background
Icon=capturfacil
OnlyShowIn=GNOME;
NoDisplay=true
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=5
""")
write('usr/share/icons/hicolor/scalable/apps/capturfacil.svg', (BASE / 'icon.svg').read_text())
write('usr/share/doc/capturfacil/README.md', (BASE / 'README.md').read_text())
# Run only trusted package code, as each session owner, never user code as root.
# Offline sessions are handled by the per-user recovery autostart entry.
write('DEBIAN/prerm', '''#!/bin/sh
set -eu
case "${1:-}" in
  remove|deconfigure)
    for runtime in /run/user/[0-9]*; do
      [ -d "$runtime" ] || continue
      uid=${runtime##*/}
      [ "$uid" -ge 1000 ] 2>/dev/null || continue
      [ -S "$runtime/bus" ] || continue
      entry=$(getent passwd "$uid") || continue
      username=$(printf '%s' "$entry" | cut -d: -f1)
      userhome=$(printf '%s' "$entry" | cut -d: -f6)
      runuser -u "$username" -- env HOME="$userhome" XDG_CONFIG_HOME="$userhome/.config" \\
        XDG_RUNTIME_DIR="$runtime" DBUS_SESSION_BUS_ADDRESS="unix:path=$runtime/bus" \\
        /usr/bin/python3 /usr/share/capturfacil/shortcuts.py --restore || true
    done
    ;;
esac
exit 0
''', 0o755)
write('DEBIAN/postinst', '''#!/bin/sh
set -e
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
exit 0
''', 0o755)
write('DEBIAN/postrm', '''#!/bin/sh
set -e
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
fi
exit 0
''', 0o755)
archive = ROOT / 'usr/share/doc/capturfacil/source.tar.gz'
with tarfile.open(archive, 'w:gz') as tf:
    for name in ['src', 'tests', 'build.py', 'README.md', 'icon.svg']:
        tf.add(BASE / name, arcname='capturfacil/' + name,
               filter=lambda item: None if '__pycache__' in item.name else item)
(ROOT / 'DEBIAN/control').write_text((ROOT / 'DEBIAN/control').read_text() +
    f'Installed-Size: {sum(p.stat().st_size for p in ROOT.rglob("*") if p.is_file()) // 1024 + 1}\n')
for directory in ROOT.rglob('*'):
    if directory.is_dir():
        directory.chmod(0o755)
ROOT.chmod(0o755)
archive.chmod(0o644)
(BASE / 'dist').mkdir(exist_ok=True)
output = BASE / 'dist/capturfacil_0.1.2_all.deb'
subprocess.run(['dpkg-deb', '--root-owner-group', '--build', str(ROOT), str(output)], check=True)
print(output)
