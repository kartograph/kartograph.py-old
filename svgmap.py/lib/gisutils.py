#encoding: utf-8
"""
A collection of functions useful for gis-related tasks
"""


def area(pts, earthrad=6371):
	from math import radians as rad, sin, cos, asin, sqrt, pi, tan, atan
	pihalf = pi * .5

	n = len(pts)
	sum = 0
	for j in range(0,n):
		k = (j+1)%n
		if j == 0:
			lam1 = rad(pts[j][0])
			beta1 = rad(pts[j][1])
			cosB1 = cos(beta1)
		else:
			lam1 = lam2
			beta1 = beta2
			cosB1 = cosB2
		lam2 = rad(pts[k][0])
		beta2 = rad(pts[k][1])
		cosB2 = cos(beta2)
		
		if lam1 != lam2:
			hav = haversine( beta2 - beta1 ) + cosB1 * cosB2 * haversine(lam2 - lam1)
			a = 2 * asin(sqrt(hav))
			b = pihalf - beta2
			c = pihalf - beta1
			s = 0.5 * (a+b+c)
			t = tan(s*0.5) * tan((s-a)*0.5) * tan((s-b)*0.5) * tan((s-c)*0.5)
			excess = abs(4*atan(sqrt(abs(t))))
			if lam2 < lam1:
				excess = -excess
			sum += excess
	return abs(sum)*earthrad*earthrad
			
	
def haversine(x):
	"""
	implementation taken from
	http://forum.worldwindcentral.com/showthread.php?t=20724
	
	algorithm expects a list of [lng,lat] pairs in degrees
	"""
	from math import cos
	return ( 1.0 - cos(x) ) / 2.0

	
	
def shape_area(shape):
	"""
	computes the area of a shapefile shape
	"""
	parts = shape.parts[:]
	parts.append(len(shape.points))
	A = 0
	for i in range(len(parts)-1):
		pts = shape.points[parts[i]:parts[i+1]]
		A += area(pts)
	return A
	


def shape_center(shape):
	"""
	computes the center of gravity of a shapefile multi-polygon
	"""
	from Polygon import Polygon
	parts = shape.parts[:]
	parts.append(len(shape.points))
	
	# check for countries that cross the 180° longitude
	
	far_east = False
	far_west = False
	
	for i in range(len(parts)-1):
		pts = shape.points[parts[i]:parts[i+1]]
		if len(pts) == 0: continue
		if pts[0][0] < -90:
			far_west = True
		if pts[0][0] > 90:
			far_east = True
	
	poly = Polygon()
	for i in range(len(parts)-1):
		pts = shape.points[parts[i]:parts[i+1]]
		if far_east and far_west:
			# correct points
			for j in range(len(pts)):
				if pts[j][0] < 0: pts[j][0] += 360
		poly.addContour(pts)
	return poly.center()
	

def polygon_center(polygon):
	"""
	computes the center of gravity of a gisutils.Polygon
	"""
	from Polygon import Polygon as Poly
	pts = []
	for pt in polygon.points:
		pts.append((pt.x, pt.y))
	poly = Poly(pts)
	c = poly.center()
	return Point(c[0], c[1])
	

	
import math
import sys


		
def unify(polygons):
	"""
	Replaces duplicate points with an instance of the 
	same point
	"""
	point_store = {}
	out_polygons = []
	kept = 0
	removed = 0
	for poly in polygons:
		new_points = []
		for pt in poly.points:
			pid = '%f-%f' % (pt.x, pt.y)
			if pid in point_store:
				point = point_store[pid]
				if point.two: point.three = True
				else: point.two = True
				removed += 1
			else:
				point = pt
				kept += 1
				point_store[pid] = pt
			new_points.append(point)
		poly.points = new_points
	#print 'unifying polygons removed %d duplicate points (of %d total points)'%(removed, removed+kept)			
		
		
def simplify(polygon, dist):
	"""
	Simplifies a list of polygons while maintaining
	the correct borders between each polygon
	"""
	new_points = []
	dist_sq = dist*dist
	n = len(polygon.points)
	
	kept = 0
	deleted = 0
	
	
	for i in range(0, n):
		# look for the first "inner" points and mark them as not deletable
		j = (i+1)%n
		pt = polygon.points[i]
		npt = polygon.points[j]
		if pt.two and not npt.two:
			pt.keep = True
		if not pt.two and npt.two:
			npt.keep = True
	
	for i in range(0, n):
		pt = polygon.points[i]
		if i == 0 or i == n-1:
			pt.simplified = True
			lpt = pt
		else:
			d = (pt.x - lpt.x) * (pt.x - lpt.x) + (pt.y - lpt.y) * (pt.y - lpt.y)
			if d > dist_sq or not pt.isDeletable():
				lpt = pt
				kept += 1
			else:
				pt.deleted = True
				deleted += 1
			pt.simplified = True
	
	


class Point(object):
	"""
	Point used
	"""
	def __init__(self, x, y):
		self.x = x
		self.y = y
		self.simplified = False
		self.deleted = False
		self.two = False
		self.three = False
		self.keep = False
		
	def isDeletable(self):
		if self.keep or self.simplified or self.three: 
			return False
		return True
		

		
def smartBounds(shape, proj, thresh=0.25):
	"""
	Computes a smart bounding box for a given shape.
	
	For calculation of the bbox only those polygons are used
	which area is larger than thresh*max_area. For instance, for
	a threshold > 0.2 this would remove Alaska and Hawaii from 
	the bounding box of the United States, while keeping both big
	islands of New Zeal inside.
	"""
	import sys
	
	points = shape.points
	parts = shape.parts[:]
	parts.append(len(points))
	
	# find largest polygon
	areas = []
	for j in range(0,len(parts)-1):
		pts = points[parts[j]:parts[j+1]]
		a = area(pts)
		areas.append(a)
	max_area = max(areas)
	
	# filter polygons
	largest_polys = []
	for j in range(0,len(parts)-1):
		if areas[j] >= max_area * 0.25:
			largest_polys.append(points[parts[j]:parts[j+1]])
	
	# compute bounding box of largest polygons
	min_lat, max_lat, min_lon, max_lon = (90,-90,180,-180)
	
	for poly in largest_polys:
		for (lon,lat) in poly:
			if lon < min_lon:
				min_lon = lon
				min_lon_lat = lat
			if lon > max_lon:
				max_lon = lon
				max_lon_lat = lat
			if lat < min_lat:
				min_lat = lat
				min_lat_lon = lon
			if lat > max_lat:
				max_lat = lat
				max_lat_lon = lon
	pts = [(min_lon, min_lon_lat), (max_lon, max_lon_lat), (min_lat_lon, min_lat), (max_lat_lon, max_lat)]
	
	print pts
	
	xmin = ymin = sys.maxint
	xmax = ymax = sys.maxint * -1
	
	for (lon, lat) in pts:
		x,y = proj(lon, lat)
		xmin = min(xmin, x)
		xmax = max(xmax, x)
		ymin = min(ymin, y)
		ymax = max(ymax, y)
	
	return (xmin, ymax, xmax-xmin, ymin-ymax)
	
import sys

class Bounds2D(object):
	"""
	2D bounding box
	"""
	def __init__(self, width=None, height=None, left=0, top=0):
		if width == None:
			self.xmin = sys.maxint
			self.xmax = sys.maxint*-1
		else:
			self.xmin = self.left = left
			self.xmax = self.right = left + width
			self.width = width
		if height == None:
			self.ymin = sys.maxint
			self.ymax = sys.maxint*-1
		else:
			self.ymin = self.top = top
			self.ymax = self.bottom = height + top
			self.height = height
			
	def update(self, pt):
		self.xmin = min(self.xmin, pt.x)
		self.ymin = min(self.ymin, pt.y)
		self.xmax = max(self.xmax, pt.x)
		self.ymax = max(self.ymax, pt.y)
		
		self.left = self.xmin
		self.top = self.ymin
		self.right = self.xmax
		self.bottom = self.ymax
		self.width = self.xmax - self.xmin
		self.height = self.ymax - self.ymin
		
	def intersects(self, bbox):
		return bbox.left < self.right and bbox.right > self.left and bbox.top < self.bottom and bbox.bottom > self.top
		
	def __str__(self):
		return '[%.2f, %.2f, %.2f, %.2f]' % (self.left, self.top, self.width, self.height)

	
class Polygon(object):
	"""
	A polygon, identified by an unique id
	takes points as list of points
	
	mode can be one of the following:
	- 'tuple'  for access via x = point[0], y = point[1] 
	- 'object' for access via x = point['x'], y = point['y']
	- 'class'  for access via x = point.x, y = point.y
	- 'point'  for access via point.x
	"""
	def __init__(self, id, points, mode='tuple', data=None):
		self.id = id
		self.bbox = Bounds2D()
		if data != None: self.data = data
		else: self.data = {}
		new_points = []
		for pt in points:
			if mode == 'tuple':
				pt = Point(pt[0],pt[1])
			elif mode == 'object':
				pt = Point(pt['x'],pt['y'])
			elif mode == 'class':
				pt = Point(pt.x,pt.y)
			elif mode == 'point':
				pass
			
			self.bbox.update(pt)
			new_points.append(pt)
		self.points = new_points
		
		
	def svgPolygonPoints(self, useIntegers=True):
		"""
		returns the points in SVG <polygon points="..." />
		"""
		svg_poly_points = ''
		for pt in self.points:
			if pt.deleted: continue
			if useIntegers:
				svg_poly_points += '%d,%d '%(int(pt.x),int(pt.y))
			else:
				svg_poly_points += '%f,%f '%(pt.x,pt.y)	
		return svg_poly_points
		
	
	def svgPathString(self, useInt=True):
		"""
		returns the path string representation of this polygon
		"""
		ps = ''
		for pt in self.points:
			if pt.deleted: continue #ignore deleted points
			if ps == '': ps = 'M'
			else: ps += 'L'
			if useInt:
				ps += '%d,%d' % (round(pt.x), round(pt.y))
			else:
				ps += '%.3f,%.3f' % (pt.x, pt.y)
		ps += 'Z' # close path
		return ps


	
class View(object):
	"""
	translates a point to a view
	"""
	def __init__(self, bbox, width, height, padding=0):
		self.bbox = bbox
		self.width = width
		self.padding = padding
		self.height = height
		self.scale = min((width-padding*2) / bbox.width, (height-padding*2) / bbox.height)
		
	def project(self, pt):
		s = self.scale
		bbox = self.bbox
		h = self.height
		w = self.width
		x = (pt.x - bbox.left) * s + (w - bbox.width * s) * .5
		y = (pt.y - bbox.top) * s + (h - bbox.height * s) * .5
		return Point(x, y)
		
	def __str__(self):
		return 'View(w=%f, h=%f, pad=%f, scale=%f, bbox=%s)' % (self.width, self.height, self.padding, self.scale, self.bbox)
		
		
def clipToRect(polygon, bbox):
	"""
	clips a polygon to a given bounding box
	takes in a gisutils.Polygon and gisutils.Bounds2D
	"""
	from Polygon import Polygon as Poly
	from Polygon.Shapes import Rectangle
	
	# step 1: create polygons from input data structures
	rect = Rectangle(bbox.width, bbox.height)
	rect.shift(bbox.left, bbox.top)
	
	pts = []
	for p in polygon.points:
		if p.deleted:
			# skip deleted points
			continue
		pts.append((p.x, p.y))
	
	if len(pts) < 3:
		return []
	
	poly = Poly(pts)
	
	# crop polygon to rectangle
	out = poly & rect
	
	outPolys = []
	for i in range(0, len(out)):
		outPolys.append(Polygon(polygon.id, out.contour(i), data=polygon.data))
	return outPolys
	
	
def getPolygons(shp, id, proj, view):
	parts = shp.parts[:]
	parts.append(len(shp.points))
	polys = []
	for j in range(len(parts)-1):
		pts = shp.points[parts[j]:parts[j+1]]
		lats = []
		lons = []
		for k in range(0,len(pts)):
			lats.append(pts[k][1])
			lons.append(pts[k][0])
	
		poly_points = []
		x, y = proj(lons, lats)
		for i in range(len(x)):
			pt = view.project(Point(x[i], y[i]))
			pt.y = view.height - pt.y
			poly_points.append(pt)
		polygon = Polygon(id, poly_points, mode='point')
		if polygon != None:                                                                                                                                   
			polys.append(polygon)                                                                                                                              
	return polys
	
	
	
def polygon_to_poly(polygon):
	"""
	computes the center of gravity of a shapefile multi-polygon
	"""
	from Polygon import Polygon as Poly
	pts = []
	for pt in polygon.points:
		pts.append((pt.x, pt.y))
	return Poly(pts)
	

def poly_to_polygons(poly, id='', data=None):
	out = []
	if poly == None: return out
	for i in range(len(poly)):
		pts = []
		for x,y in poly.contour(i):
			pts.append((x,y))
		out.append(Polygon(id, pts, data=data))
	return out

	
def merge_polygons(polygons, id='', data=None):
	"""
	combines polygons 
	"""
	if len(polygons) == 1:
		polygons[0].data = data
		polygons[0].id = id
		return polygons
		
	poly = polygon_to_poly(polygons[0])
	for polygon in polygons[1:]:
		poly2 = polygon_to_poly(polygon)
		poly = poly | poly2
		
	return poly_to_polygons(poly)


def restore_poly_from_path_str(path_str):
	"""
	restores a list of polygons from a SVG path string
	"""
	contours = path_str.split('Z') #last contour may be empty
	from Polygon import Polygon as Poly
	poly = Poly()
	for c_str in contours:
		if c_str.strip() != "":
			pts_str = c_str.strip()[1:].split("L")
			pts = []
			for pt_str in pts_str:
				x,y = map(float, pt_str.split(','))
				pts.append((x,y))
			poly.addContour(pts, is_clockwise(pts))
	return poly
	
	
def is_clockwise(pts):
	"""
	returns true if a given polygon is in clockwise order
	"""
	s = 0
	for i in range(len(pts)-1):
		if 'x' in pts[i]:
			x1 = pts[i].x
			y1 = pts[i].y
			x2 = pts[i+1].x
			y2 = pts[i+1].y
		else:
			x1, y1 = pts[i]
			x2, y2 = pts[i+1]
		s += (x2-x1) * (y2+y1)
	return s >= 0