#!/bin/sh
# xrdp resets the keyboard to the client's single layout on every reconnect;
# put back us,ru with Alt+Shift whenever that happens.
want_layout="us,ru"
apply() { setxkbmap -model pc105 -layout "$want_layout" -option '' -option grp:ctrl_space_toggle; }
apply
while sleep 3; do
  cur=$(setxkbmap -query 2>/dev/null) || continue
  echo "$cur" | grep -q "^layout: *$want_layout\$" && echo "$cur" | grep -q 'grp:ctrl_space_toggle' || apply
done
