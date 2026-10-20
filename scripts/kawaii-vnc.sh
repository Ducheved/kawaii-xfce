#!/bin/sh
# VNC for the current desktop, reachable only from the home LAN.
# Password: ~/.vnc/passwd (create it with `tigervncpasswd` or `x11vnc -storepasswd`).
# TigerVNC viewer: connect to <laptop-ip>::5901 (encrypted with TLS automatically).
#
# Settings (override in the environment or edit here):
LAN_IFACE="${KAWAII_VNC_IFACE:-$(ip -4 route show default | awk '{print $5; exit}')}"
VNC_PORT="${KAWAII_VNC_PORT:-5901}"

pgrep -u "$USER" -x 'x11vnc|X0tigervnc' >/dev/null && exit 0
DISP="${DISPLAY:-:10}"
LAN_IP=$(ip -4 -o addr show "$LAN_IFACE" 2>/dev/null | awk '{sub("/.*","",$4); print $4; exit}')
LAN_NET=$(echo "$LAN_IP" | cut -d. -f1-3).
[ -n "$LAN_IP" ] || exit 1

if command -v X0tigervnc >/dev/null; then
  # TigerVNC's own server: UTF-8 clipboard (Russian text, emoji) and raw
  # keycodes, so the layout follows the server's own layout switch.
  # Listens only on the LAN address (its HostsFile option segfaults in 1.15).
  # If it dies right away, fall back to x11vnc below.
  start=$(date +%s)
  X0tigervnc -display "$DISP" -rfbport "$VNC_PORT" -interface "$LAN_IP" \
    -PasswordFile "$HOME/.vnc/passwd" -AlwaysShared \
    -PollingCycle 15 -MaxProcessorUsage 50 -RawKeyboard \
    -SendPrimary=0 -SetPrimary=0 \
    >"$HOME/.cache/x0vncserver.log" 2>&1
  [ $(( $(date +%s) - start )) -gt 10 ] && exit 0
fi
exec x11vnc -norc -display "$DISP" -auth "$HOME/.Xauthority" \
  -rfbport "$VNC_PORT" -allow "$LAN_NET,127.0.0.1" -usepw -forever -shared \
  -threads -wait 5 -defer 5 -speeds lan -xkb -noprimary -nosetprimary \
  -o "$HOME/.cache/x11vnc.log"
