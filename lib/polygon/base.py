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

	def addContour(self, contour, isHole=False):
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
		
	def svgPath(self):
		raise NotImplementedError