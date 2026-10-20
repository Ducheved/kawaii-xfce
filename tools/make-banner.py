#!/usr/bin/env python3
# Draws preview/banner.png (1280x640, GitHub social preview size) from the
# wallpaper and the widget/menu previews.
import math, os, sys
import gi
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gdk, GdkPixbuf, Pango, PangoCairo
import cairo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1280, 640
PINK, LAV, CREAM, MINT = (1, .475, .776), (.741, .576, .976), (1, .92, .97), (.545, 1, .776)


def rrect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()


def text(cr, s, x, y, font, color, alpha=1.0, align='left'):
    lay = PangoCairo.create_layout(cr)
    lay.set_font_description(Pango.FontDescription(font))
    lay.set_markup(s, -1)
    w, h = lay.get_pixel_size()
    if align == 'right':
        x -= w
    cr.set_source_rgba(*color, alpha)
    cr.move_to(x, y)
    PangoCairo.show_layout(cr, lay)
    return w, h


def image(cr, path, x, y, w, radius=18, shadow=True):
    pb = GdkPixbuf.Pixbuf.new_from_file(path)
    h = pb.get_height() * w / pb.get_width()
    pb = pb.scale_simple(int(w), int(h), GdkPixbuf.InterpType.HYPER)
    if shadow:
        for i in range(14, 0, -2):
            rrect(cr, x - i / 2, y - i / 2 + 6, w + i, h + i, radius + i / 2)
            cr.set_source_rgba(0, 0, 0, 0.035)
            cr.fill()
    cr.save()
    rrect(cr, x, y, w, h, radius)
    cr.clip()
    Gdk.cairo_set_source_pixbuf(cr, pb, x, y)
    cr.paint()
    cr.restore()
    rrect(cr, x, y, w, h, radius)
    cr.set_source_rgba(*PINK, 0.55)
    cr.set_line_width(2)
    cr.stroke()
    return h


s = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
cr = cairo.Context(s)
wall = GdkPixbuf.Pixbuf.new_from_file(f'{ROOT}/wallpapers/kawaii-night.png')
wall = wall.scale_simple(int(W * 1.25), int(W * 1.25 * 9 / 16), GdkPixbuf.InterpType.HYPER)
Gdk.cairo_set_source_pixbuf(cr, wall, -W * 0.25, -60)
cr.paint()
g = cairo.LinearGradient(0, 0, W, 0)
g.add_color_stop_rgba(0, .07, .04, .13, .82)
g.add_color_stop_rgba(.55, .07, .04, .13, .35)
g.add_color_stop_rgba(1, .07, .04, .13, 0)
cr.set_source(g)
cr.paint()

# fake top bar
cr.rectangle(0, 0, W, 34)
cr.set_source_rgba(.10, .05, .16, .92)
cr.fill()
text(cr, '♡', 16, 6, 'Quicksand Bold 13', PINK)
text(cr, "<span foreground='#ff9ad5'>(◕‿◕)</span>  <span foreground='#ff9ad5'>♡ cpu</span> 13%  "
         "<span foreground='#c9a8ff'>✿ ram</span> 48%  <span foreground='#9dffc6'>☁ 51°</span>      "
         "✿ Tue 20 Oct  ♡ 18:44", W - 18, 7, 'Quicksand Bold 11', CREAM, align='right')

text(cr, 'Kawaii XFCE', 70, 150, 'Quicksand Bold 60', CREAM)
text(cr, '✿ dark plum &amp; pink desktop for XFCE 4.20', 74, 245, 'Quicksand Medium 20', PINK)
y = 310
for line in ('♡  cat widget with live system stats',
             '✿  task list &amp; stats on the panel',
             '☁  styled start menu, pink folders',
             '⚡  fast over RDP / VNC'):
    text(cr, line, 78, y, 'Quicksand Medium 17', CREAM, 0.9)
    y += 40
text(cr, '(｡•ᴗ•｡)', 78, 500, 'Quicksand Bold 22', LAV)

image(cr, f'{ROOT}/preview/menu.png', 760, 90, 300)
image(cr, f'{ROOT}/preview/widget.png', 990, 250, 250, radius=26)

s.write_to_png(sys.argv[1] if len(sys.argv) > 1 else f'{ROOT}/preview/banner.png')
