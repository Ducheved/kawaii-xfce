#!/bin/bash
# Kawaii XFCE: dark plum + pink desktop for XFCE 4.20 (X11).
#
#   ./install.sh            theme, fonts, wallpaper, widget, terminal, menu styles
#   ./install.sh --panel    also rebuild the top panel (replaces your current one!)
#   ./install.sh --keys     also add Windows-like shortcuts and us,ru on Ctrl+Space
#   ./install.sh --vnc      also autostart the LAN-only VNC server
#
# Everything it overwrites is backed up to ~/.config/kawaii-backup/<date>/.
set -e
cd "$(dirname "$0")"
REPO=$(pwd)
BIN="$HOME/.local/bin"
WALL_DIR="$HOME/Pictures/Kawaii-Wallpapers"
BACKUP="$HOME/.config/kawaii-backup/$(date +%Y%m%d-%H%M%S)"
WANT_PANEL=0 WANT_KEYS=0 WANT_VNC=0
for a in "$@"; do
  case "$a" in
    --panel) WANT_PANEL=1 ;; --keys) WANT_KEYS=1 ;; --vnc) WANT_VNC=1 ;;
    *) echo "unknown option: $a" >&2; exit 1 ;;
  esac
done

say() { printf '\033[38;2;255;121;198m✿\033[0m %s\n' "$*"; }
xq() { xfconf-query -c "$1" -p "$2" -n -t "$3" -s "$4"; }

need=""
for cmd in xfconf-query python3 genmon:/usr/lib/x86_64-linux-gnu/xfce4/panel/plugins/libgenmon.so; do
  case "$cmd" in *:*) [ -e "${cmd#*:}" ] || need="$need ${cmd%%:*}" ;; *) command -v "$cmd" >/dev/null || need="$need $cmd" ;; esac
done
python3 -c "import gi, cairo; gi.require_version('Gtk','3.0')" 2>/dev/null || need="$need python3-gi"
if [ -n "$need" ]; then
  echo "Missing:$need. Install the dependencies first (see README):" >&2
  echo "  sudo apt install fonts-quicksand fonts-firacode fonts-noto-color-emoji papirus-icon-theme breeze-cursor-theme xfce4-whiskermenu-plugin xfce4-genmon-plugin xfce4-cpugraph-plugin xfce4-clipman xfce4-taskmanager python3-gi python3-gi-cairo python3-cairo gir1.2-gtk-3.0 oneko" >&2
  exit 1
fi

say "Backing up current settings to $BACKUP"
mkdir -p "$BACKUP"
for c in xsettings xfwm4 xfce4-panel xfce4-desktop xfce4-keyboard-shortcuts keyboard-layout; do
  xfconf-query -c "$c" -lv > "$BACKUP/$c.txt" 2>/dev/null || true
done
for f in .config/gtk-3.0/gtk.css .config/fontconfig/fonts.conf .config/xfce4/terminal/terminalrc .face; do
  [ -e "$HOME/$f" ] && mkdir -p "$BACKUP/$(dirname "$f")" && cp -a "$HOME/$f" "$BACKUP/$f"
done

say "Scripts → $BIN"
mkdir -p "$BIN"
install -m 755 scripts/kawaii-widget.py scripts/kawaii-stats.sh "$BIN/"

say "Config files (GTK styles, fonts, terminal)"
mkdir -p ~/.config/gtk-3.0 ~/.config/fontconfig ~/.config/xfce4/terminal
cp config/gtk-3.0/gtk.css ~/.config/gtk-3.0/gtk.css
cp config/fontconfig/fonts.conf ~/.config/fontconfig/fonts.conf
cp config/xfce4/terminal/terminalrc ~/.config/xfce4/terminal/terminalrc
fc-cache -f >/dev/null 2>&1 || true

say "Wallpaper and avatar"
mkdir -p "$WALL_DIR"
cp wallpapers/kawaii-night.png "$WALL_DIR/"
cp wallpapers/avatar-cat.png ~/.face
for k in $(xfconf-query -c xfce4-desktop -l | grep -E '/(last-image|image-path)$'); do
  xfconf-query -c xfce4-desktop -p "$k" -s "$WALL_DIR/kawaii-night.png"
done
for k in $(xfconf-query -c xfce4-desktop -l | grep -E 'image-style$'); do
  xfconf-query -c xfce4-desktop -p "$k" -s 5
done

say "Pink Papirus folders"
sh tools/make-pink-papirus.sh || true

say "Theme, fonts, cursor, compositor"
if [ -d "$HOME/.themes/Dracula" ] || [ -d /usr/share/themes/Dracula ]; then
  xq xsettings /Net/ThemeName string Dracula
  xq xfwm4 /general/theme string Dracula
else
  echo "  (Dracula GTK theme not found — get it from https://github.com/dracula/gtk, then rerun)"
fi
[ -d "$HOME/.local/share/icons/Papirus-Dark-Pink" ] && xq xsettings /Net/IconThemeName string Papirus-Dark-Pink
xq xsettings /Gtk/FontName string "Quicksand Medium 10"
fc-list | grep -q "FiraCode Nerd Font" && mono="FiraCode Nerd Font 10" || mono="Fira Code 10"
xq xsettings /Gtk/MonospaceFontName string "$mono"
xq xsettings /Gtk/CursorThemeName string breeze_cursors
xq xfwm4 /general/title_font string "Quicksand Bold 10"
# The compositor is off on purpose: it's the biggest win over RDP/VNC, and the
# widget fakes its transparency from the wallpaper.
xq xfwm4 /general/use_compositing bool false
for s in show_dock_shadow show_frame_shadow show_popup_shadow; do xq xfwm4 "/general/$s" bool false; done

say "Autostart: widget, cat, clipboard history"
mkdir -p ~/.config/autostart
for f in autostart/*.desktop; do
  name=$(basename "$f")
  case "$name" in kawaii-vnc.desktop) [ $WANT_VNC = 1 ] || continue ;; sea-xkb.desktop) [ $WANT_KEYS = 1 ] || continue ;; esac
  sed "s|@BIN@|$BIN|g" "$f" > ~/.config/autostart/"$name"
done
command -v oneko >/dev/null || command -v /usr/games/oneko >/dev/null || rm -f ~/.config/autostart/oneko.desktop

if [ $WANT_KEYS = 1 ]; then
  say "Windows-like shortcuts, us,ru on Ctrl+Space"
  install -m 755 scripts/kawaii-xkb-guard.sh "$BIN/"
  C=xfce4-keyboard-shortcuts
  xq $C /commands/custom/Super_L string xfce4-popup-whiskermenu
  xq $C '/commands/custom/<Super>e' string thunar
  xq $C '/commands/custom/<Super>l' string xflock4
  xq $C '/commands/custom/<Super>r' string 'xfce4-appfinder -c'
  xq $C '/commands/custom/<Super>i' string xfce4-settings-manager
  xq $C '/commands/custom/<Super>v' string xfce4-clipman-history
  xq $C '/commands/custom/<Super><Shift>s' string 'xfce4-screenshooter -r -c'
  xq $C '/commands/custom/<Primary><Shift>Escape' string xfce4-taskmanager
  xq $C '/xfwm4/custom/<Super>d' string show_desktop_key
  xq $C '/xfwm4/custom/<Super>Up' string maximize_window_key
  xq $C '/xfwm4/custom/<Super>Down' string hide_window_key
  xq $C '/xfwm4/custom/<Super>Left' string tile_left_key
  xq $C '/xfwm4/custom/<Super>Right' string tile_right_key
  xq $C '/xfwm4/custom/<Super>Tab' string cycle_windows_key
  xq keyboard-layout /Default/XkbLayout string us,ru
  xq keyboard-layout /Default/XkbOptions/Group string grp:ctrl_space_toggle
fi

[ $WANT_VNC = 1 ] && { say "VNC launcher (LAN only)"; install -m 755 scripts/kawaii-vnc.sh "$BIN/"; }

if [ $WANT_PANEL = 1 ]; then
  say "Rebuilding the top panel"
  bash tools/apply-panel.sh "$BIN"
fi

say "Starting the widget"
pkill -u "$USER" -f "$BIN/kawaii-widget.py" 2>/dev/null || true
setsid nohup "$BIN/kawaii-widget.py" >/dev/null 2>&1 </dev/null &

say "Done! Restart open apps (or log out and back in) to pick up the new fonts. Nya~ (◕‿◕)"
