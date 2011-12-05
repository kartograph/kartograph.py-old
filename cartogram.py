#!/usr/bin/env python2.7

from lib.cartogram import Cartogram
from lib import proj



cg = Cartogram()
cg.loadCSV('us-states-2.csv', 'hasc', 'pop')
cg.project(proj.LAEA(lon0=-98.6,lat0=40))
cg.layout(100)
cg.toSVG()
