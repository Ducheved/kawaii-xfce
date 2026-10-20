#!/bin/sh
# Builds ~/.local/share/icons/Papirus-Dark-Pink: Papirus-Dark with pink
# folders, without sudo (symlinks to the system Papirus pink variants).
set -e
SRC=/usr/share/icons/Papirus
D="$HOME/.local/share/icons/Papirus-Dark-Pink"
[ -d "$SRC" ] || { echo "papirus-icon-theme is not installed" >&2; exit 1; }
rm -rf "$D"; mkdir -p "$D"
for sizedir in "$SRC"/*x*; do
  sz=$(basename "$sizedir"); pl="$sizedir/places"; [ -d "$pl" ] || continue
  mkdir -p "$D/$sz/places"
  for f in "$pl"/folder-violet*.svg "$pl"/user-violet*.svg; do
    [ -e "$f" ] || continue
    b=$(basename "$f"); target=$(echo "$b" | sed 's/violet/pink/')
    [ -e "$pl/$target" ] || continue
    ln -sf "$pl/$target" "$D/$sz/places/$(echo "$b" | sed 's/-violet//')"
  done
done
dirs=$(cd "$D" && ls -d */places | tr '\n' ',' | sed 's/,$//')
{
  echo "[Icon Theme]"; echo "Name=Papirus-Dark-Pink"
  echo "Inherits=Papirus-Dark,Papirus,hicolor"; echo "Directories=$dirs"
  for d in $(echo "$dirs" | tr ',' ' '); do
    printf '\n[%s]\nContext=Places\nSize=%s\nType=Fixed\n' "$d" "${d%%x*}"
  done
} > "$D/index.theme"
gtk-update-icon-cache -f "$D" >/dev/null 2>&1 || true
echo "Papirus-Dark-Pink built in $D"
