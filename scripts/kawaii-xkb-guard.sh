#!/bin/sh
# xrdp resets the keyboard to the client's single layout on every reconnect;
# put back us,ru with the layout-switch keys whenever that happens.
# Switch: Ctrl+Space or Alt+Shift (Win+Space is an XFCE shortcut that runs
# kawaii-next-layout.py, because XKB allows only one toggle on Space).
want_layout="us,ru"
want_options="grp:ctrl_space_toggle,grp:alt_shift_toggle"
apply() {
  setxkbmap -model pc105 -layout "$want_layout" -option '' \
    $(echo "$want_options" | tr ',' '\n' | sed 's/^/-option /')
}
apply
while sleep 3; do
  cur=$(setxkbmap -query 2>/dev/null) || continue
  echo "$cur" | grep -q "^layout: *$want_layout\$" &&
    echo "$cur" | grep -q "^options: *$want_options\$" || apply
done
