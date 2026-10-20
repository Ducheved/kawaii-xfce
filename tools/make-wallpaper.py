import cairo, math, random, sys
W,H=2560,1440
random.seed(7)
s=cairo.ImageSurface(cairo.FORMAT_RGB24,W,H); c=cairo.Context(s)
g=cairo.LinearGradient(0,0,0,H)
g.add_color_stop_rgb(0,0.07,0.04,0.13); g.add_color_stop_rgb(0.6,0.13,0.06,0.22); g.add_color_stop_rgb(1,0.24,0.08,0.28)
c.set_source(g); c.paint()
# soft glow blobs
for x,y,r,col in [(1900,380,700,(1,.47,.78)),(500,1200,800,(.74,.58,.98)),(1300,1500,600,(1,.6,.85))]:
    rg=cairo.RadialGradient(x,y,0,x,y,r); rg.add_color_stop_rgba(0,*col,.16); rg.add_color_stop_rgba(1,*col,0)
    c.set_source(rg); c.paint()
# stars
for _ in range(260):
    x,y=random.uniform(0,W),random.uniform(0,H*0.8); r=random.choice([1,1,1.5,2,2.5])
    c.set_source_rgba(1,.9,1,random.uniform(.3,.9)); c.arc(x,y,r,0,2*math.pi); c.fill()
def sparkle(x,y,r,col,a=1):
    c.save(); c.translate(x,y); c.set_source_rgba(*col,a)
    pts=[(0,-r),(r,0),(0,r),(-r,0)]
    c.move_to(*pts[0])
    for i in range(4):
        nx,ny=pts[(i+1)%4]; c.curve_to(0,0,0,0,nx,ny)
    c.close_path(); c.fill(); c.restore()
for x,y,r,col in [(420,260,26,(1,.75,.9)),(2200,1050,20,(.85,.75,1)),(760,640,14,(1,.85,.95)),(1700,200,18,(.9,.8,1)),(2350,300,12,(1,.7,.9)),(300,900,16,(.9,.8,1))]:
    sparkle(x,y,r,col,.9)
# moon (crescent) with cute face
mx,my,mr=1880,420,170
rg=cairo.RadialGradient(mx,my,mr*.8,mx,my,mr*2.2); rg.add_color_stop_rgba(0,1,.8,.93,.35); rg.add_color_stop_rgba(1,1,.8,.93,0)
c.set_source(rg); c.arc(mx,my,mr*2.2,0,2*math.pi); c.fill()
c.push_group()
c.set_source_rgb(1,.88,.95); c.arc(mx,my,mr,0,2*math.pi); c.fill()
c.set_operator(cairo.OPERATOR_CLEAR); c.arc(mx+95,my-60,mr*.92,0,2*math.pi); c.fill()
c.pop_group_to_source(); c.paint()
# face on crescent
c.set_source_rgb(.25,.12,.3); c.set_line_width(6); c.set_line_cap(cairo.LINE_CAP_ROUND)
for ex in (mx-115,mx-60):
    c.arc(ex,my+30,13,math.pi*1.1,math.pi*1.9); c.stroke()  # closed happy eyes ^ ^
c.arc(mx-88,my+62,12,0.15*math.pi,0.85*math.pi); c.stroke()
c.set_source_rgba(1,.5,.7,.6)
for ex in (mx-135,mx-38):
    c.save(); c.translate(ex,my+62); c.scale(1.6,1); c.arc(0,0,11,0,2*math.pi); c.restore(); c.fill()
# cat silhouette on hills
c.set_source_rgb(.06,.03,.1)
c.move_to(0,H); c.line_to(0,1250)
c.curve_to(500,1150,900,1290,1400,1230); c.curve_to(1900,1170,2200,1210,W,1150); c.line_to(W,H); c.close_path(); c.fill()
cx,cy=1500,1225
c.save(); c.translate(cx,cy)
c.move_to(-70,0); c.curve_to(-80,-120,80,-120,70,0); c.close_path(); c.fill()   # body
c.arc(0,-130,48,0,2*math.pi); c.fill()  # head
for sx in(-1,1):
    c.move_to(sx*44,-150); c.line_to(sx*40,-205); c.line_to(sx*12,-172); c.close_path(); c.fill()
c.set_line_width(14); c.set_line_cap(cairo.LINE_CAP_ROUND)
c.move_to(60,-10); c.curve_to(150,-10,150,-110,110,-120); c.stroke()  # tail
c.restore()
# little hearts floating
def heart(x,y,sz,col,a):
    c.save(); c.translate(x,y); c.scale(sz/20,sz/20); c.set_source_rgba(*col,a)
    c.move_to(0,6); c.curve_to(-20,-8,-8,-22,0,-10); c.curve_to(8,-22,20,-8,0,6); c.fill(); c.restore()
for x,y,sz,a in [(1560,1020,22,.9),(1600,960,16,.7),(1640,905,11,.5),(1200,300,14,.5),(600,450,12,.45),(2100,800,15,.5)]:
    heart(x,y,sz,(1,.47,.78),a)
s.write_to_png(sys.argv[1] if len(sys.argv) > 1 else 'kawaii-night.png')
