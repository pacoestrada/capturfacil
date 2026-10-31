"""Capture commands. Never use X11 capture for a Wayland session."""
import shutil


def capture_commands(mode, path, x11=False, compatible=False):
    commands = []
    if x11 and not compatible and mode in ('monitor', 'screen'):
        scrot = shutil.which('scrot')
        if scrot:
            commands.append([scrot, '-z', '-o', str(path)])
    gnome = ['gnome-screenshot', '-f', str(path)]
    if mode == 'area':
        gnome.append('-a')
    elif mode == 'window':
        gnome.extend(['-w', '-d', '3'])
    commands.append(gnome)
    return commands
