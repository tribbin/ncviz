#!/usr/bin/env python3

import sys, math, numpy, cairo, gi, shapefile, threading, time
from scipy import interpolate

try:
    gi.require_foreign("cairo")
except ImportError:
    print("cairo missing :(")

# Performance and output
th    = 6         # Number of threads.
outx  = 1920      # Pixels X.
outy  = 1080      # Pixels Y.
gs    = 20        # Grid size in pixels.

# Coordinates
lat0 = -15.0     # Starting position: X
latn =  13.0     # Number of X steps: max 113 in DCSMv6
latd = lat0-latn
lon0 =  59.5     # Starting position: y
lonn =  48.5     # Number of Y steps: max 85 in DCSMv6
lond = lon0-lonn
ar   = (outx/outy)/(latd/lond) # Size of X compared to Y.

vs    = 1/20 # Vector size in pixels per meter/second
get   = 2
step  = 4   # Increase to draw less vectors.

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
tn = ds.dimensions['time'].size
u = [None for i in range(tn)]
v = [None for i in range(tn)]
tsx = numpy.arange(-15.0,13.0,0.14)
tsy = numpy.arange(48.5,59.5,0.14*ar)
for i in range(0,tn):
  dsut = interpolate.interp2d(ds.variables['longitude'][:],ds.variables['latitude'][:],ds.variables['u10'][i], kind='cubic')
  dsvt = interpolate.interp2d(ds.variables['longitude'][:],ds.variables['latitude'][:],ds.variables['v10'][i], kind='cubic')
  u[i] = dsut(tsx,tsy)
  v[i] = dsvt(tsx,tsy)
  dsut = dsvt = None
ds.close()
bbox = [-15,43,13,57.5]


# Get countries from shapefile.
sf = shapefile.Reader("lib/countries.shp")
shs = sf.shapes()
countries = []

for sh in shs:
  #if (sh.bbox[0] > bbox[0] and sh.bbox[2] < bbox[2] and sh.bbox[1] > bbox[1] and sh.bbox[3] > bbox[3]):
  countries.append(sh)

# Plot countries.
overlay = cairo.ImageSurface(cairo.FORMAT_ARGB32, int((xn-x0)*gs), (yn-y0)*gs)
ctx2 = cairo.Context(overlay)
ctx2.set_line_width(3)
ctx2.set_line_join(cairo.LINE_JOIN_BEVEL)
for c in countries:
  ctx2.move_to((c.points[0][0]-bbox[0])*ar*60*10,-(c.points[0][1])*60)
  for i, p in enumerate(c.points):
    if i in c.parts:
      ctx2.move_to((p[0]-bbox[0])*60*4*ar,-(p[1]-bbox[3])*60*4)
    else:
      ctx2.line_to((p[0]-bbox[0])*60*4*ar,-(p[1]-bbox[3])*60*4)
  #ctx2.set_source_rgba(1, 1, 1, 0.5)
  #ctx2.set_operator(cairo.Operator.SOURCE)
  #ctx2.fill_preserve()
  ctx2.set_operator(cairo.Operator.SOURCE)
  ctx2.set_source_rgba(1, 1, 1, 0.5)
  ctx2.stroke()

# Clean up memory.
countries = sf = shs = None
xRange = range(0,xn)
yRange = range(0,yn)

# Background of vector area.
def drawArea(x,y,ms,ctx):
    ctx.set_source_rgb(3-(ms/7.5), 1-(ms/15), 1-(ms/15))
    ctx.rectangle(x*gs,2160-y*gs,gs,-gs)
    ctx.fill()   

# The vector itself.
def drawVector(x,y,u,v,ms,ctx):
    y = 107-y
    ctx.set_line_width(4)
    ctx.set_source_rgba(1, 1, 1, ms/15)
    ctx.move_to(x*gs+(gs)/2,y*gs+gs/2)
    ctx.rel_line_to(u*gs*vs*step,-v*gs*vs*step)
    ctx.close_path()
    ctx.stroke()
    ctx.set_source_rgb(1, 1, 1)
    ctx.arc(x*gs+(gs)/2+(u)*gs*vs*step,y*gs+gs/2+(-v)*gs*vs*step,5*(ms/20),0,2*math.pi)
    ctx.fill()

# Black -> Areas -> Vectors.
def draw(image, ctx, n):
    global overlay
    ctx.set_source_rgb(0, 0, 0)
    ctx.paint()
    for y in xRange:
      for x in yRange:
        td[n]['zero'] = time.time()
        ut = u[t[n]][x][y]
        vt = v[t[n]][x][y]
        td[n]['matrix'] += time.time() - td[n]['zero']
        td[n]['zero'] = time.time()
        ms = math.sqrt(ut*ut+vt*vt)
        td[n]['math'] += time.time() - td[n]['zero']
        td[n]['zero'] = time.time()
        drawArea(y,x,ms,ctx)
        td[n]['area'] += time.time() - td[n]['zero']
    ctx.set_source_surface(overlay)
    ctx.paint()
    for y in xRange:
      for x in yRange:
        if (x%step == y%step==get):
          td[n]['zero'] = time.time()
          ut = u[t[n]][x][y]
          vt = v[t[n]][x][y]
          td[n]['matrix'] += time.time() - td[n]['zero']
          td[n]['zero'] = time.time()
          ms = math.sqrt(ut*ut+vt*vt)
          td[n]['math'] += time.time() - td[n]['zero']
          td[n]['zero'] = time.time()
          drawVector(y,x,ut,vt,ms,ctx)
          td[n]['vector'] += time.time() - td[n]['zero']
    td[n]['zero'] = time.time()
    image.write_to_png("output/wind_"+str(format(t[n], '05'))+".png");
    td[n]['write'] = time.time() - td[n]['zero']

t=[0 for i in range(th)]
td=[0 for i in range(th)]
ctx=[0 for i in range(th)]
image=[0 for i in range(th)]

def worker(n,m):
    while (t[n] < tn):
      if (t[n]%m==n):
        draw(image[n],ctx[n],n)
        print("t:%d written by %d/%d" % (t[n],n+1,m))
      t[n] += 1

workers = list()
tt = time.time()


for index in range(th):
    t[index] = 0 # Time-step counter at 0.
    image[index] = cairo.ImageSurface(cairo.FORMAT_ARGB32, int((xn-x0)*gs), (yn-y0)*gs)
    ctx[index] = cairo.Context(image[index])
    ctx[index].set_antialias(cairo.Antialias.FAST)
    td[index] = {'zero':0,'matrix':0,'math':0,'area':0,'vector':0,'write':0}
    w = threading.Thread(target=worker, args=(index,th), daemon=True)
    workers.append(w)
    w.start()

for w in workers:
    w.join()

for index, tdn in enumerate(td):
    print("%d: matrix=%.2f, math=%.2f, area=%.2f, vector=%.2f, write=%.2f" % (index+1,tdn['matrix'],tdn['math'],tdn['area'],tdn['vector'],tdn['write']))

print("total: %.2f seconds" % (time.time()-tt))
