#!/usr/bin/env python3
# Switch to the next keyboard layout group (bound to Win+Space in XFCE;
# XKB can't put Win+Space and Ctrl+Space toggles on the same key).
import ctypes, ctypes.util

class XkbStateRec(ctypes.Structure):
    _fields_ = [('group', ctypes.c_ubyte), ('locked_group', ctypes.c_ubyte),
                ('base_group', ctypes.c_ushort), ('latched_group', ctypes.c_ushort),
                ('mods', ctypes.c_ubyte), ('base_mods', ctypes.c_ubyte),
                ('latched_mods', ctypes.c_ubyte), ('locked_mods', ctypes.c_ubyte),
                ('compat_state', ctypes.c_ubyte), ('grab_mods', ctypes.c_ubyte),
                ('compat_grab_mods', ctypes.c_ubyte), ('lookup_mods', ctypes.c_ubyte),
                ('compat_lookup_mods', ctypes.c_ubyte), ('ptr_buttons', ctypes.c_ushort)]

XKB_USE_CORE_KBD = 0x0100
x = ctypes.CDLL(ctypes.util.find_library('X11'))
x.XOpenDisplay.restype = ctypes.c_void_p
dpy = x.XOpenDisplay(None)
if not dpy:
    raise SystemExit('no display')
dpy = ctypes.c_void_p(dpy)
state = XkbStateRec()
x.XkbGetState(dpy, XKB_USE_CORE_KBD, ctypes.byref(state))
# number of groups from the layout list, e.g. "us,ru" -> 2
import subprocess
layouts = [l for l in subprocess.run(['setxkbmap', '-query'], capture_output=True, text=True)
           .stdout.split('layout:')[-1].split('\n')[0].strip().split(',') if l]
n = max(len(layouts), 1)
x.XkbLockGroup(dpy, XKB_USE_CORE_KBD, (state.group + 1) % n)
x.XFlush(dpy)
x.XCloseDisplay(dpy)
