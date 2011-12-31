"""
    kartograph - a svg mapping library 
    Copyright (C) 2011  Gregor Aisch

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


class AbstractPolygon(object):
	"""
	all polygon implementation will implement this interface
	"""
	def __init__(self, contours=None, data=None):
		self.data = data
		
	def __len__(self):
		raise NotImplementedError
		
	def __getitem__(self, key):
		raise NotImplementedError

	def addContour(self, contour):
		raise NotImplementedError
		
	def __and__(self, other):
		raise NotImplementedError

	def __or__(self, other):
		raise NotImplementedError

	def __add__(self, other):
		return self.__or__(other)
		
	def __sub__(self, other):
		raise NotImplementedError
				
	def area(self):
		raise NotImplementedError
	
	def center(self):
		raise NotImplementedError
		
	def isInside(self, x, y):
		raise NotImplementedError
		


class PolyPolygon(AbstractPolygon):
	"""
	http://pypi.python.org/pypi/Polygon/2.0.4
	http://www.j-raedler.de/projects/polygon/
	"""
	def __init__(self, contours=None, data=None):
		AbstractPolygon.__init__(self, contours=contours, data=data)
		from Polygon import Polygon as Poly
		self.poly = Poly()
		for c in contours:
			self.addContour(c)
	
	def __len__(self):
		return len(self.poly)
		
	def __getitem__(self, key):
		return self.poly[key]

	def addContour(self, contour):
		self.poly.addContour(contour)
				
	def __and__(self, other):
		from Polygon import Polygon as Poly
		res = self.poly & other.poly
		return PolyPolygon(list(res), self.data)

	def __or__(self, other):
		res = self.poly | other.poly
		return PolyPolygon(list(res), self.data)
		
	def __sub__(self, other):
		res = self.poly - other.poly
		return PolyPolygon(list(res), self.data)
		
	def area(self):
		return self.poly.area()
	
	def center(self):
		return self.poly.center()
		
	def isInside(self, x, y):
		return self.poly.isInside(x,y)	
		
		

Polygon = PolyPolygon



if __name__ == "__main__":
	
	p = Polygon([[(0,0),(30,0),(15,30)]])
	print 'p', p.area()
	q = Polygon([[(10,5),(30,0),(15,20)]])
	print 'q', q.area()
	print 'p+q', (p+q).area()
	print 'p-q', (p-q).area()
	print 'p&q', (p&q).area()	
	print 'p|q', (p|q).area()