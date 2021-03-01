#!/usr/bin/env python3

import sys, math, cairo, gi

try:
    gi.require_foreign("cairo")
except ImportError:
    print("cairo missing :(")

n = int(sys.argv[1]) # thread number of this worker
m = int(sys.argv[2]) # total number of threads

nr    = 8784 # Total number of time steps.
ar    = 0.6  # Size of X compared to Y.
x0    = 0    # Starting position: X
y0    = 27   # Starting position: y
xtot  = 113  # Number of X steps: max 113 in DCSMv6
ytot  = 38   # Number of Y steps: max 85 in DCSMv6
gs    = 57   # Grid size in pixels.
vs    = 1/15 # Vector size in pixels per meter/second
step  = 1    # Increase to draw less vectors.

# Get vector subset from file.
from netCDF4 import Dataset
ds = Dataset("download.nc", "r", format="NETCDF4")
u = ds['u10'][0:nr,y0:y0+ytot,x0:x0+xtot]
v = ds['v10'][0:nr,y0:y0+ytot,x0:x0+xtot]
ds.close()

xRange = range(0,xtot)
yRange = range(0,ytot)
t = 0 # Time/frame counter.

image = cairo.ImageSurface(cairo.FORMAT_ARGB32, int((xtot-x0)*gs*ar), ytot*gs)
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
    ctx.stroke()
    ctx.close_path()
    ctx.set_source_rgb(1, 1, 1)
    ctx.arc(x*gs+(gs*ar)/2+(u)*gs*vs*step,y*gs+gs/2+(-v)*gs*vs*step,5*(ms/20),0,2*math.pi)
    ctx.fill()

# Black -> Areas -> Vectors.
def draw(image, ctx):
    global t
    if (t%m==n): # For multi-threading.
      ctx.set_source_rgb(0, 0, 0)
      ctx.paint()
      for y in xRange:
        for x in yRange:
          ut = u[t,y,x]
          vt = v[t,y,x]
          ms = math.sqrt(ut*ut+vt*vt)
          drawArea(x*ar,y,ms,ctx)
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
