#!/usr/bin/env python3
# Kawaii desktop widget: clock, greeting and system stats drawn with cairo.
import glob, math, os, time, shutil, subprocess
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('PangoCairo', '1.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Pango, PangoCairo

W, H = 380, 470
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
        self.blink = 0
        self.connect('draw', self.on_draw)
        self.connect('destroy', Gtk.main_quit)
        GLib.timeout_add(2000, self.tick)
        self.tick()

    def tick(self):
        self.stats.update()
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
        return False


if __name__ == '__main__':
    Widget().show_all()
    Gtk.main()
