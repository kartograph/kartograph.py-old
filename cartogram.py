#!/usr/bin/env python2.7

from lib.cartogram import Cartogram
from lib import proj

cg = Cartogram()
cg.loadCSV('../misc/bw/gemeinden.csv', 'key', 'pop')
cg.project(proj.LAEA(lon0=9,lat0=48))
cg.layout(1000)
cg.toSVG()