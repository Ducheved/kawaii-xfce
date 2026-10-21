#!/usr/bin/env python3
# Kawaii desktop widget: clock, greeting and system stats drawn with cairo.
import glob, math, os, time, shutil, subprocess
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('PangoCairo', '1.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Pango, PangoCairo

W, H = 380, 640
X, Y = 60, 90          # position on screen
FONT = 'Quicksand'
NAME = os.environ.get('KAWAII_NAME') or os.environ.get('USER', 'nya').capitalize()

PINK = (1.0, 0.475, 0.776)
LAV = (0.741, 0.576, 0.976)
MINT = (0.545, 1.0, 0.776)
SKY = (0.545, 0.914, 0.992)
CREAM = (1.0, 0.92, 0.97)
BG = (0.10, 0.06, 0.16)


def rrect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()


class Stats:
    def __init__(self):
        self.prev = self._cpu_times()
        self.net_prev = self._net_bytes()
        self.t_prev = time.time()
        self.cpu = self.mem = self.disk = self.temp = 0
        self.down = self.up = 0.0

    @staticmethod
    def _cpu_times():
        v = list(map(int, open('/proc/stat').readline().split()[1:8]))
        return sum(v), v[3] + v[4]

    @staticmethod
    def _net_bytes():
        rx = tx = 0
        for line in open('/proc/net/dev').readlines()[2:]:
            name, data = line.split(':', 1)
            name = name.strip()
            if name == 'lo' or name.startswith(('docker', 'veth', 'br-')):
                continue
            f = data.split()
            rx += int(f[0]); tx += int(f[8])
        return rx, tx

    def update(self):
        tot, idle = self._cpu_times()
        dt, di = tot - self.prev[0], idle - self.prev[1]
        self.prev = (tot, idle)
        self.cpu = 100 * (dt - di) / dt if dt else 0
        mi = {l.split(':')[0]: int(l.split()[1]) for l in open('/proc/meminfo')}
        self.mem = 100 * (mi['MemTotal'] - mi['MemAvailable']) / mi['MemTotal']
        du = shutil.disk_usage('/')
        self.disk = 100 * du.used / du.total
        try:
            self.temp = int(open(TEMP_FILE).read()) / 1000
        except (OSError, TypeError):
            self.temp = 0
        now = time.time(); rx, tx = self._net_bytes()
        el = max(now - self.t_prev, 0.1)
        self.down = (rx - self.net_prev[0]) / el
        self.up = (tx - self.net_prev[1]) / el
        self.net_prev, self.t_prev = (rx, tx), now


def find_cpu_temp():
    for hw in glob.glob('/sys/class/hwmon/hwmon*'):
        try:
            if open(f'{hw}/name').read().strip() in ('coretemp', 'k10temp', 'zenpower'):
                return f'{hw}/temp1_input'
        except OSError:
            pass
    zones = glob.glob('/sys/class/thermal/thermal_zone*/temp')
    return zones[0] if zones else None


TEMP_FILE = find_cpu_temp()


# Friendly app names for the "who eats" list: process name -> label.
APP_NAMES = {
    'claude-desktop': 'Claude', 'claude': 'Claude Code', 'chrome': 'Chrome',
    'code': 'VS Code', 'Xorg': 'Экран (Xorg)', 'X0tigervnc': 'VNC', 'x11vnc': 'VNC',
    'xrdp': 'RDP', 'wrapper-2.0': 'Панель', 'xfce4-panel': 'Панель',
    'AmneziaVPN': 'AmneziaVPN', 'AmneziaVPN-serv': 'AmneziaVPN', 'amneziawg-go': 'AmneziaVPN',
    'dockerd': 'Docker', 'containerd': 'Docker', 'thunar': 'Файлы', 'xfdesktop': 'Рабочий стол',
    'xfce4-terminal': 'Терминал', 'firefox-esr': 'Firefox', 'Isolated Web Co': 'Firefox',
    'go': 'Go', 'compile': 'Go', 'eslint': 'ESLint',
}
NODE_HINTS = (('svelte', 'MCP Svelte'), ('figma', 'MCP Figma'), ('eslint', 'ESLint'),
              ('vitest', 'Vitest'), ('tsc', 'TypeScript'), ('vite', 'Vite'))


class Procs:
    """Per-app CPU (% of the whole machine) and RAM, grouped by friendly name."""
    def __init__(self):
        self.prev = {}        # pid -> cpu ticks
        self.labels = {}      # pid -> label (cmdline is read once per pid)
        self.prev_total = None
        self.ncpu = os.cpu_count() or 1
        self.page = os.sysconf('SC_PAGE_SIZE')
        self.top_cpu, self.top_mem = [], []

    def label(self, pid, comm):
        lab = self.labels.get(pid)
        if lab is None:
            lab = APP_NAMES.get(comm)
            if lab is None and comm in ('node', 'MainThread', 'npm', 'npm exec', 'python3', 'python'):
                try:
                    cmd = open(f'/proc/{pid}/cmdline', 'rb').read().replace(b'\0', b' ').decode(errors='ignore')
                except OSError:
                    cmd = ''
                if 'kawaii-widget' in cmd:
                    lab = 'виджет ♡'
                else:
                    lab = next((n for h, n in NODE_HINTS if h in cmd), 'Node' if 'node' in cmd or 'npm' in cmd else comm)
            self.labels[pid] = lab = lab or comm
        return lab

    def update(self):
        total = sum(map(int, open('/proc/stat').readline().split()[1:8]))
        dt = (total - self.prev_total) if self.prev_total else 0
        self.prev_total = total
        cpu, mem, seen = {}, {}, {}
        for d in os.listdir('/proc'):
            if not d.isdigit():
                continue
            pid = int(d)
            try:
                raw = open(f'/proc/{d}/stat').read()
                rss = int(open(f'/proc/{d}/statm').read().split()[1]) * self.page
            except OSError:
                continue
            comm = raw[raw.index('(') + 1:raw.rindex(')')]
            f = raw[raw.rindex(')') + 2:].split()
            ticks = int(f[11]) + int(f[12])
            seen[pid] = ticks
            if rss == 0:
                continue          # kernel threads
            lab = self.label(pid, comm)
            mem[lab] = mem.get(lab, 0) + rss
            if dt and pid in self.prev:
                cpu[lab] = cpu.get(lab, 0) + 100 * (ticks - self.prev[pid]) / dt
        self.prev = seen
        self.labels = {p: l for p, l in self.labels.items() if p in seen}
        self.top_cpu = sorted(cpu.items(), key=lambda kv: -kv[1])[:4]
        self.top_mem = sorted(mem.items(), key=lambda kv: -kv[1])[:4]


def gib(b):
    return f'{b / 2**30:.1f} ГБ' if b >= 2**30 else f'{b / 2**20:.0f} МБ'


def human(bps):
    for unit in ('B', 'K', 'M', 'G'):
        if bps < 1024:
            return f'{bps:.0f}{unit}/s' if unit == 'B' else f'{bps:.1f}{unit}/s'
        bps /= 1024
    return f'{bps:.1f}T/s'


def wallpaper_path():
    try:
        out = subprocess.run(['xfconf-query', '-c', 'xfce4-desktop', '-l', '-v'],
                             capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    for line in out.splitlines():
        key, _, val = line.partition(' ')
        if key.endswith('/last-image') and 'workspace0' in key and os.path.isfile(val.strip()):
            return val.strip()
    return None


def load_backdrop(path, screen):
    """Piece of the wallpaper (zoomed to fill the screen) right behind the widget."""
    try:
        pb = GdkPixbuf.Pixbuf.new_from_file(path)
    except GLib.Error:
        return None
    sw, sh = screen.get_width(), screen.get_height()
    k = max(sw / pb.get_width(), sh / pb.get_height())
    out = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, W, H)
    ox = (pb.get_width() * k - sw) / 2 + X
    oy = (pb.get_height() * k - sh) / 2 + Y
    pb.scale(out, 0, 0, W, H, -ox, -oy, k, k, GdkPixbuf.InterpType.BILINEAR)
    return out


def uptime():
    s = int(float(open('/proc/uptime').read().split()[0]))
    h, m = s // 3600, s % 3600 // 60
    return f'{h} ч {m} мин' if h else f'{m} мин'


class Widget(Gtk.Window):
    def __init__(self):
        super().__init__(title='kawaii-widget')
        self.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        self.set_keep_below(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_decorated(False)
        self.set_accept_focus(False)
        self.stick()
        self.set_app_paintable(True)
        screen = self.get_screen()
        # Without a compositor an RGBA window turns black, so fake the
        # transparency by painting the wallpaper behind the card ourselves.
        self.backdrop = None
        self.wall = None
        if screen.is_composited() and screen.get_rgba_visual():
            self.set_visual(screen.get_rgba_visual())
        else:
            self.wall = wallpaper_path()
            self.backdrop = self.wall and load_backdrop(self.wall, screen)
        screen.connect('composited-changed', lambda *_: os.execv(__file__, [__file__]))
        self.set_default_size(W, H)
        self.move(X, Y)
        self.stats = Stats()
        self.procs = Procs()
        self.blink = 0
        self.connect('draw', self.on_draw)
        self.connect('destroy', Gtk.main_quit)
        GLib.timeout_add(2000, self.tick)
        self.tick()

    def tick(self):
        self.stats.update()
        self.procs.update()
        self.blink = (self.blink + 1) % 6
        self.ticks = getattr(self, 'ticks', 0) + 1
        if self.wall is not None and self.ticks % 30 == 0:   # wallpaper changed?
            path = wallpaper_path()
            if path and path != self.wall:
                self.wall, self.backdrop = path, load_backdrop(path, self.get_screen())
        self.queue_draw()
        return True

    def text(self, cr, s, x, y, size, color, weight='Bold', align='left', alpha=1.0):
        lay = PangoCairo.create_layout(cr)
        lay.set_font_description(Pango.FontDescription(f'{FONT} {weight} {size}'))
        lay.set_text(s, -1)
        w, h = lay.get_pixel_size()
        if align == 'center':
            x -= w / 2
        elif align == 'right':
            x -= w
        cr.set_source_rgba(*color, alpha)
        cr.move_to(x, y)
        PangoCairo.show_layout(cr, lay)
        return w, h

    def heart(self, cr, x, y, s, color, a=1):
        cr.save(); cr.translate(x, y); cr.scale(s / 20, s / 20)
        cr.set_source_rgba(*color, a)
        cr.move_to(0, 6); cr.curve_to(-20, -8, -8, -22, 0, -10); cr.curve_to(8, -22, 20, -8, 0, 6)
        cr.fill(); cr.restore()

    def cat(self, cr, cx, cy, mood):
        # round cat head with ears
        cr.set_source_rgb(*CREAM)
        for sx in (-1, 1):
            cr.move_to(cx + sx * 34, cy - 12); cr.line_to(cx + sx * 40, cy - 50); cr.line_to(cx + sx * 10, cy - 34)
            cr.close_path(); cr.fill()
        cr.arc(cx, cy, 40, 0, 2 * math.pi); cr.fill()
        cr.set_source_rgba(*PINK, 0.8)
        for sx in (-1, 1):
            cr.move_to(cx + sx * 32, cy - 20); cr.line_to(cx + sx * 36, cy - 42); cr.line_to(cx + sx * 16, cy - 32)
            cr.close_path(); cr.fill()
        ink = (0.2, 0.1, 0.25)
        cr.set_source_rgb(*ink); cr.set_line_width(3.2); cr.set_line_cap(1)
        if mood == 'busy':          # > <
            for sx in (-1, 1):
                ex = cx + sx * 15
                cr.move_to(ex - 6 * sx, cy - 8); cr.line_to(ex + 5 * sx, cy - 3); cr.line_to(ex - 6 * sx, cy + 2); cr.stroke()
        elif self.blink == 0 or mood == 'sleepy':   # closed eyes ^ ^ / blink
            for sx in (-1, 1):
                cr.arc(cx + sx * 15, cy - 2, 6, math.pi * 1.15, math.pi * 1.85); cr.stroke()
        else:
            for sx in (-1, 1):
                cr.arc(cx + sx * 15, cy - 3, 5.5, 0, 2 * math.pi); cr.fill()
                cr.set_source_rgb(1, 1, 1); cr.arc(cx + sx * 15 + 2, cy - 5, 1.8, 0, 2 * math.pi); cr.fill()
                cr.set_source_rgb(*ink)
        # mouth w
        cr.set_line_width(2.4)
        cr.arc(cx - 4, cy + 8, 4, 0.1 * math.pi, 0.9 * math.pi); cr.stroke()
        cr.arc(cx + 4, cy + 8, 4, 0.1 * math.pi, 0.9 * math.pi); cr.stroke()
        # blush
        cr.set_source_rgba(*PINK, 0.55)
        for sx in (-1, 1):
            cr.save(); cr.translate(cx + sx * 26, cy + 8); cr.scale(1.5, 1); cr.arc(0, 0, 5.5, 0, 2 * math.pi); cr.restore(); cr.fill()
        # whiskers
        cr.set_source_rgba(*ink, 0.6); cr.set_line_width(1.5)
        for sx in (-1, 1):
            for dy in (-3, 4):
                cr.move_to(cx + sx * 33, cy + 4 + dy); cr.line_to(cx + sx * 50, cy + 2 + dy * 1.6); cr.stroke()

    def bar(self, cr, x, y, w, label, icon, pct, color, value_text):
        self.text(cr, f'{icon} {label}', x, y, 11, color)
        self.text(cr, value_text, x + w, y, 11, CREAM, align='right')
        by = y + 24
        rrect(cr, x, by, w, 12, 6); cr.set_source_rgba(1, 1, 1, 0.08); cr.fill()
        fw = max(12, w * min(pct, 100) / 100)
        rrect(cr, x, by, fw, 12, 6)
        cr.set_source_rgba(*color, 0.9); cr.fill()
        # paw at the end of the bar
        px = x + fw - 6
        cr.set_source_rgba(1, 1, 1, 0.85)
        cr.arc(px, by + 6, 2.6, 0, 2 * math.pi); cr.fill()

    def on_draw(self, _w, cr):
        if self.backdrop:
            Gdk.cairo_set_source_pixbuf(cr, self.backdrop, 0, 0); cr.paint()
        else:
            cr.set_operator(0); cr.paint(); cr.set_operator(2)  # clear, then OVER
        s = self.stats
        # card
        rrect(cr, 6, 6, W - 12, H - 12, 28)
        cr.set_source_rgba(*BG, 0.72); cr.fill_preserve()
        cr.set_source_rgba(*PINK, 0.45); cr.set_line_width(2); cr.stroke()

        mood = 'busy' if s.cpu >= 75 or s.temp >= 85 else ('sleepy' if s.cpu < 8 else 'ok')
        self.cat(cr, 72, 92, mood)
        self.heart(cr, 122, 48, 14, PINK, 0.9)
        self.heart(cr, 134, 34, 9, LAV, 0.7)

        t = time.localtime()
        self.text(cr, time.strftime('%H:%M', t), W - 34, 30, 40, CREAM, align='right')
        days = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля',
                  'августа', 'сентября', 'октября', 'ноября', 'декабря']
        self.text(cr, f'{t.tm_mday} {months[t.tm_mon - 1]}, {days[t.tm_wday]}', W - 34, 92, 11, LAV,
                  weight='Medium', align='right')
        hr = t.tm_hour
        greet = ('доброй ночи ☾' if hr < 5 else 'доброе утро ☀' if hr < 12
                 else 'добрый день ✿' if hr < 18 else 'добрый вечер ♡' if hr < 23 else 'пора спать ☾')
        msg = {'busy': 'ня! жарко работаю (＞﹏＜)', 'ok': 'всё хорошо, мяу (◕‿◕)',
               'sleepy': 'мурр… отдыхаю (￣ω￣)'}[mood]
        self.text(cr, f'{greet}, {NAME}', W / 2, 150, 13, PINK, align='center')
        self.text(cr, msg, W / 2, 174, 10, CREAM, weight='Medium', align='center', alpha=0.85)

        x, w = 34, W - 68
        y = 212
        self.bar(cr, x, y, w, 'процессор', '♡', s.cpu, PINK, f'{s.cpu:.0f}%'); y += 52
        self.bar(cr, x, y, w, 'память', '✿', s.mem, LAV, f'{s.mem:.0f}%'); y += 52
        self.bar(cr, x, y, w, 'диск', '☁', s.disk, SKY, f'{s.disk:.0f}%'); y += 52
        self.bar(cr, x, y, w, 'температура', '♨', s.temp, MINT, f'{s.temp:.0f}°C'); y += 56

        self.text(cr, f'↓ {human(s.down)}', x, y, 10, SKY, weight='Medium')
        self.text(cr, f'↑ {human(s.up)}', W / 2, y, 10, PINK, weight='Medium', align='center')
        self.text(cr, f'⏱ {uptime()}', x + w, y, 10, LAV, weight='Medium', align='right')

        # who eats the most
        y += 34
        cr.set_source_rgba(*PINK, 0.25); cr.set_line_width(1)
        cr.move_to(x, y - 10); cr.line_to(x + w, y - 10); cr.stroke()
        self.text(cr, 'кто ест больше всех ♡', W / 2, y, 11, PINK, align='center')
        y += 28
        col = (w - 16) / 2
        self.top_list(cr, x, y, col, '♡ процессор', PINK,
                      [(n, v, f'{v:.0f}%') for n, v in self.procs.top_cpu],
                      max([25] + [v for _, v in self.procs.top_cpu]))
        mem_total = self.mem_total
        self.top_list(cr, x + col + 16, y, col, '✿ память', LAV,
                      [(n, v, gib(v)) for n, v in self.procs.top_mem], mem_total)
        return False

    @property
    def mem_total(self):
        if not hasattr(self, '_mem_total'):
            self._mem_total = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
        return self._mem_total

    def top_list(self, cr, x, y, w, title, color, rows, full):
        self.text(cr, title, x, y, 10, color)
        y += 22
        for name, val, shown in rows:
            name = name if len(name) <= 13 else name[:12] + '…'
            self.text(cr, name, x, y, 9, CREAM, weight='Medium', alpha=0.9)
            self.text(cr, shown, x + w, y, 9, color, weight='Bold', align='right')
            rrect(cr, x, y + 17, w, 4, 2); cr.set_source_rgba(1, 1, 1, 0.07); cr.fill()
            fw = max(4, w * min(val / full, 1)) if full else 4
            rrect(cr, x, y + 17, fw, 4, 2); cr.set_source_rgba(*color, 0.8); cr.fill()
            y += 28


if __name__ == '__main__':
    Widget().show_all()
    Gtk.main()
