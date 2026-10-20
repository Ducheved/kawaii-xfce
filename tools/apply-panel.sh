#!/bin/bash
# Rebuilds panel-1 as the kawaii top bar:
#   ♡ menu | open windows ........ (◕‿◕) cpu/ram/temp | cpu graph | tray | volume | power | clock
# Plugin ids match config/gtk-3.0/gtk.css (#tasklist-24), keep them in sync.
set -e
BIN="${1:-$HOME/.local/bin}"
C=xfce4-panel
xq() { xfconf-query -c $C -p "$1" -n -t "$2" -s "$3"; }
rgba() { xfconf-query -c $C -p "$1" -n -t double -t double -t double -t double -s "$2" -s "$3" -s "$4" -s "$5"; }

# The panel saves its in-memory state on exit, so change settings while it's down.
xfce4-panel --quit 2>/dev/null || true
sleep 2

for id in $(xfconf-query -c $C -l | grep -oE '^/plugins/plugin-[0-9]+$' | grep -oE '[0-9]+$'); do
  xfconf-query -c $C -p "/plugins/plugin-$id" -r -R
done
xfconf-query -c $C -p /panels -n -t int -s 1 -a 2>/dev/null || true

P=/panels/panel-1
xq $P/position string 'p=6;x=0;y=0'
xq $P/position-locked bool true
xq $P/length uint 100
xq $P/size uint 42
xq $P/icon-size uint 22
xq $P/background-style uint 1
rgba $P/background-rgba 0.10 0.05 0.16 0.88
xq /panels/dark-mode bool true

xq /plugins/plugin-1 string whiskermenu
W=/plugins/plugin-1
xq $W/button-icon string emblem-favorite
xq $W/menu-width int 640
xq $W/menu-height int 620
xq $W/view-mode int 1
xq $W/item-icon-size int 2
xq $W/category-icon-size int 1
xq $W/default-category int 0
xq $W/launcher-show-description bool false
xq $W/hover-switch-category bool true
xq $W/position-search-alternate bool true
xq $W/profile-shape int 0
for c in settings lockscreen logout restart shutdown; do xq $W/show-command-$c bool true; done
for c in switchuser suspend hibernate menueditor logoutuser; do xq $W/show-command-$c bool false; done

xq /plugins/plugin-2 string separator
xq /plugins/plugin-2/style uint 0

xq /plugins/plugin-24 string tasklist
T=/plugins/plugin-24
xq $T/show-labels bool true
xq $T/flat-buttons bool true
xq $T/grouping bool false
xq $T/show-handle bool false
xq $T/include-all-workspaces bool true
xq $T/show-wireframes bool false
xq $T/middle-click uint 1

xq /plugins/plugin-25 string separator
xq /plugins/plugin-25/style uint 0
xq /plugins/plugin-25/expand bool true

xq /plugins/plugin-21 string genmon
mkdir -p ~/.config/xfce4/panel
cat > ~/.config/xfce4/panel/genmon-21.rc <<EOF
Command=$BIN/kawaii-stats.sh
UseLabel=0
Text=
UpdatePeriod=2000
Font=Quicksand Bold 11
EOF

xq /plugins/plugin-22 string cpugraph
G=/plugins/plugin-22
rgba $G/foreground-1 1.0 0.475 0.776 1
rgba $G/foreground-2 0.741 0.576 0.976 1
rgba $G/foreground-3 1.0 0.84 0.925 1
rgba $G/foreground-user 1.0 0.475 0.776 1
rgba $G/foreground-system 0.741 0.576 0.976 1
rgba $G/foreground-nice 1.0 0.84 0.925 1
rgba $G/foreground-iowait 0.545 0.914 0.992 1
rgba $G/background 0.17 0.106 0.24 0.6
xq $G/bars int 0
xq $G/color-mode int 1
xq $G/size int 70
xq $G/border int 1
xq $G/command string xfce4-taskmanager

xq /plugins/plugin-23 string separator
xq /plugins/plugin-23/style uint 0

xq /plugins/plugin-5 string systray
xq /plugins/plugin-5/square-icons bool true
xq /plugins/plugin-6 string pulseaudio
xq /plugins/plugin-7 string power-manager-plugin
xq /plugins/plugin-8 string clock
xq /plugins/plugin-8/mode uint 2
xq /plugins/plugin-8/digital-layout uint 3
xq /plugins/plugin-8/digital-time-font string 'Quicksand Bold 12'
xq /plugins/plugin-8/digital-time-format string '✿ %a %d %b  ♡ %H:%M'

ids=(1 2 24 25 21 22 23 5 6 7 8)
args=(); for i in "${ids[@]}"; do args+=(-t int -s "$i"); done
xfconf-query -c $C -p $P/plugin-ids -n -a "${args[@]}"

xfconf-query -c xfwm4 -p /general/workspace_count -s 1

setsid nohup xfce4-panel >/dev/null 2>&1 </dev/null &
echo "panel rebuilt"
