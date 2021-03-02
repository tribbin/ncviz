#!/usr/bin/env python3

import sys, math, cairo, gi, shapefile

try:
    gi.require_foreign("cairo")
except ImportError:
    print("cairo missing :(")

nr    = 8784 # Total number of time steps.
ar    = 0.6  # Size of X compared to Y.
x0    = 0    # Starting position: X
xn    = 113  # Number of X steps: max 113 in DCSMv6
y0    = 27   # Starting position: y
yn    = 65   # Number of Y steps: max 85 in DCSMv6
gs    = 57   # Grid size in pixels.
vs    = 1/15 # Vector size in pixels per meter/second
step  = 1    # Increase to draw less vectors.

if (len(sys.argv) == 4):
  n = int(sys.argv[2]) # thread number of this worker
  m = int(sys.argv[3]) # total number of threads
  single = False
else:
  single = True

if (len(sys.argv) > 1):
  filename = sys.argv[1]
else:
  # Select file
  import gtk
  gi.require_version("Gtk", "3.0")
  from gi.repository import Gtk
  dialog = Gtk.FileChooserDialog()
  dialog.set_title("NetCDF file")
  dialog.set_action(Gtk.FileChooserAction.OPEN)
  dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)

  # Sanity check for file selection
  if (dialog.run() == Gtk.ResponseType.OK):
    filename = dialog.get_filename()
  else:
    print("No file selected... Bye!")
    quit()

# Get vector subset from file.
print("Reading dataset: " + filename)
from netCDF4 import Dataset
ds = Dataset(filename, "r", format="NETCDF4")
u = ds['u10'][0:nr,y0:yn,x0:xn]
v = ds['v10'][0:nr,y0:yn,x0:xn]
bbox = [-15,43,13,57.5]
ds.close()

# Get countries from shapefile.
sf = shapefile.Reader("lib/countries.shp")
shs = sf.shapes()
countries = []

for sh in shs:
  #if (sh.bbox[0] > bbox[0] and sh.bbox[2] < bbox[2] and sh.bbox[1] > bbox[1] and sh.bbox[3] > bbox[3]):
  countries.append(sh)

# Plot countries.
overlay = cairo.ImageSurface(cairo.FORMAT_ARGB32, int((xn-x0)*gs*ar), (yn-y0)*gs)
ctx2 = cairo.Context(overlay)
ctx2.set_line_width(3)
ctx2.set_line_join(cairo.LINE_JOIN_BEVEL)
for c in countries:
  ctx2.move_to((c.points[0][0]-bbox[0])*ar*gs*10,-(c.points[0][1])*gs)
  for i, p in enumerate(c.points):
    if i in c.parts:
      ctx2.move_to((p[0]-bbox[0])*gs*4*ar,-(p[1]-bbox[3])*gs*4)
    else:
      ctx2.line_to((p[0]-bbox[0])*gs*4*ar,-(p[1]-bbox[3])*gs*4)
  ctx2.set_source_rgba(1, 1, 1, 0.5)
  ctx2.set_operator(cairo.Operator.SOURCE)
  ctx2.fill_preserve()
  ctx2.set_operator(cairo.Operator.CLEAR)
  ctx2.set_source_rgb(1, 1, 1)
  ctx2.stroke()

xRange = range(0,(xn-x0))
yRange = range(0,(yn-y0))
t = 0 # Time/frame counter.

image = cairo.ImageSurface(cairo.FORMAT_ARGB32, int((xn-x0)*gs*ar), (yn-y0)*gs)
ctx = cairo.Context(image)

# Background of vector area.
def drawArea(x,y,ms,ctx):
    ctx.set_source_rgb(3-(ms/7.5), 1-(ms/15), 1-(ms/15))
    ctx.rectangle(x*gs,y*gs,gs,gs)
    ctx.fill()   

# The vector itself.
def drawVector(x,y,u,v,ms,ctx):
    ctx.set_line_width(4)
    ctx.set_source_rgba(1, 1, 1, ms/15)
    ctx.move_to(x*gs+(gs*ar)/2,y*gs+gs/2)
    ctx.rel_line_to(u*gs*vs*step,-v*gs*vs*step)
    ctx.close_path()
    ctx.stroke()
    ctx.set_source_rgb(1, 1, 1)
    ctx.arc(x*gs+(gs*ar)/2+(u)*gs*vs*step,y*gs+gs/2+(-v)*gs*vs*step,5*(ms/20),0,2*math.pi)
    ctx.fill()

# Black -> Areas -> Vectors.
def draw(image, ctx):
    global t
    global overlay
    if (single or t%m==n): # For multi-threading.
      ctx.set_source_rgb(0, 0, 0)
      ctx.paint()
      for y in yRange:
        for x in xRange:
          ut = u[t,y,x]
          vt = v[t,y,x]
          ms = math.sqrt(ut*ut+vt*vt)
          drawArea(x*ar,y,ms,ctx)
      ctx.set_source_surface(overlay)
      ctx.paint()
      for y in yRange:
        for x in xRange:
          if (x%step == y%step==0):
            ut = u[t,y,x]
            vt = v[t,y,x]
            ms = math.sqrt(ut*ut+vt*vt)
            drawVector(x*ar,y,ut,vt,ms,ctx)
      image.write_to_png("output/wind_"+str(format(t, '05'))+".png");
    t += 1

while (t < nr):
    draw(image,ctx)
