"""
    kartograph - a svg mapping library
    Copyright (C) 2011  Gregor Aisch

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


class CohenSutherland(object):
	
	INSIDE = 0
	LEFT = 1
	RIGHT = 2
	BOTTOM = 4
	TOP = 8
	
	def compute_out_code(self, bbox, x, y):
		code = self.INSIDE
		if x < bbox.left: code |= self.LEFT
		elif x > bbox.right: code |= self.RIGHT
		if y < bbox.top: code |= self.TOP
		elif y > bbox.bottom: code |= self.BOTTOM
		return code
	
	def clip(self, bbox, x0, y0, x1, y1):
		code0 = self.compute_out_code(bbox, x0, y0)
		code1 = self.compute_out_code(bbox, x1, y1)
		accept = False
		while True:
			if not (code0 | code1): 
				# Bitwise OR is 0. Trivially accept and get out of loop
				accept = True
				break	
			elif code0 & code1:
				# Bitwise AND is not 0. Trivially reject and get out of loop
				break
			else:
				# At least one endpoint is outside the clip rectangle; pick it
				cout = (code1, code0)[code0 != 0]
				# Now find the intersection point;
                # use formulas y = y0 + slope * (x - x0), x = x0 + (1 / slope) * (y - y0)
				if cout & self.TOP:
					# point is above the clip rectangle
					x = x0 + (x1 - x0) * (bbox.top - y0) / (y1 - y0)
					y = bbox.top
				elif cout & self.BOTTOM:
					# point is below the clip rectangle
					x = x0 + (x1 - x0) * (bbox.bottom - y0) / (y1 - y0)
					y = bbox.bottom
				elif cout & self.RIGHT:  
					# point is to the right of clip rectangle
					y = y0 + (y1 - y0) * (bbox.right - x0) / (x1 - x0)
					x = bbox.right
				elif cout & self.LEFT:
					# point is to the left of clip rectangle
					y = y0 + (y1 - y0) * (bbox.left - x0) / (x1 - x0)
					x = bbox.left
				# Now we move outside point to intersection point to clip
				# and get ready for next pass.
				if cout == code0: 
					x0 = x
					y0 = y
					code0 = self.compute_out_code(bbox, x0, y0)
				else:
					x1 = x
					y1 = y
					code1 = self.compute_out_code(bbox, x1, y1)
		if accept:
			return (x0, y0, x1, y1)
			
	
class Line(object):
	def __init__(self, points):
		self.points = points
		
	def __and__(self, bbox):
		from gisutils import Bounds2D, Point
		assert isinstance(bbox, Bounds2D), 'line intersection requires Bounds2D'
		# line clipping here
		clip = CohenSutherland().clip
		pts = []
		lines = []
		last_in = False
		for i in range(len(self.points)-1):
			p0 = self.points[i]
			p1 = self.points[i+1]
			try:
				x0,y0,x1,y1 = clip(bbox, p0.x, p0.y, p1.x, p1.y)
				last_in = True
				pts.append(Point(x0, y0))
				if p1.x != x1 or p1.y != y0 or i == len(self.points)-2:
					pts.append(Point(x1, y1))
			except:
				if last_in and len(pts) > 1: 
					lines.append(Line(pts))
					pts = []
				last_in = False

		if len(pts) > 1: 
			lines.append(Line(pts))
		return lines
		
	def svgPathString(self):
		return 'M' + 'L'.join(map(str, self.points))
		

if __name__ == '__main__':
	
	from gisutils import Bounds2D, Point
	bbox = Bounds2D(left=0, top=0,width=600,height=400)
	
	from svgfig import canvas, SVG
	from random import randint, random
	from noise import pnoise1
	
	w = 1000
	h = 600
	svg = canvas(width='%dpx' % w, height='%dpx' % h, viewBox='0 0 %d %d' % (w, h), enable_background='new 0 0 %d %d' % (w, h), style='stroke-width:1px; stroke-linejoin: round;')

	svg.append(SVG('rect', x=bbox.xmin, y=bbox.ymin, width=bbox.width, height=bbox.height, fill="#eee"))
	
	clip = CohenSutherland().clip
	
	for i in range(60):
		x0 = randint(0,600)
		x1 = randint(0,600)
		y0 = randint(0,400)
		y1 = randint(0,400)
		svg.append(SVG('line', x1=x0, y1=y0, x2=x1, y2=y1, stroke='#999', stroke_width='0.2px'))
		
		try:
			x0,y0,x1,y1 = clip(bbox, x0,y0,x1,y1)
			svg.append(SVG('line', x1=x0, y1=y0, x2=x1, y2=y1, stroke='#c33', stroke_width='.2px'))
		except:
			# no intersection
			pass
	
	nx = random()*300
	ny = random()*700
	
	x = randint(0,600)
	y = randint(0,400)
	pts = []
	for i in range(5):
		pts.append(Point(x,y))
		x += 10 # pnoise1(nx)*20
		#y += pnoise1(ny)*20
		nx += .1
		ny += .1
	line = Line(pts)
	svg.append(SVG('path', d=line.svgPathString(), fill='none', stroke_width='1px', stroke='#000'))
	
	clines = line & bbox
	for cline in clines:
		svg.append(SVG('path', d=cline.svgPathString(), fill='none', stroke_width='3.5px', opacity=.5, stroke='#d00'))
	
	svg.firefox()
	
			