#!/bin/bash
# genmon: cute CPU / RAM / temp line for the xfce4 panel
st="${XDG_RUNTIME_DIR:-/tmp}/kawaii-stats.prev"
read -r _ u n s i w q sq _ < /proc/stat
tot=$((u+n+s+i+w+q+sq)); idle=$((i+w))
read -r ptot pidle 2>/dev/null < "$st" || { ptot=0; pidle=0; }
echo "$tot $idle" > "$st"
dt=$((tot-ptot)); cpu=0; [ $dt -gt 0 ] && cpu=$(( (100*(dt-(idle-pidle)))/dt ))
mem=$(awk '/MemTotal/{t=$2}/MemAvailable/{a=$2}END{printf "%d",(t-a)*100/t}' /proc/meminfo)
tf=$(grep -lE '^(coretemp|k10temp|zenpower)$' /sys/class/hwmon/hwmon*/name 2>/dev/null | head -1)
tf=${tf%/name}/temp1_input
temp=$(( $(cat "$tf" 2>/dev/null || echo 0) / 1000 ))
if   [ $cpu -ge 80 ] || [ $temp -ge 85 ]; then face="(＞﹏＜)"; fc="#ff5c8a"
elif [ $cpu -ge 40 ]; then face="(•̀ᴗ•́)"; fc="#ffe08a"
else face="(◕‿◕)"; fc="#ff9ad5"; fi
pk='#ff9ad5'; lv='#c9a8ff'; mt='#9dffc6'
echo "<txt><span foreground='$fc'>$face</span>  <span foreground='$pk'>♡ cpu</span> $cpu%  <span foreground='$lv'>✿ ram</span> $mem%  <span foreground='$mt'>☁ ${temp}°</span>  </txt>"
echo "<txtclick>xfce4-taskmanager</txtclick>"
echo "<tool>Процессор: $cpu%
Память: $mem% ($(free -h | awk '/Mem/{print $3" / "$2}'))
Температура: ${temp}°C
Диск /: $(df -h / | awk 'NR==2{print $3" / "$2}')
Работает: $(uptime -p | sed 's/up //')</tool>"
