"""
    svgmap - a simple toolset that helps creating interactive thematic maps
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

"""
Map projections used in svgmap
"""
import math 

__known_projections__ = ('ortho', 'laea', 'naturalearth')

class Proj(object):
	"""
	base class for projections
	"""
	def __init__(self, name):
		self.name = name
		self.azimuthal = False
		self.earth_rad = 6378137.0
		self.false_easting = 4321000.00
		self.false_northing = 3210000.00
		
	def plot(self, polygon, truncate=True):
		points = []
		ignore = True
		for (lat,lon) in polygon:
			vis = self._visible(lat, lon)
			if vis:
				ignore = False
			x,y = self.project(lat, lon)
			if not vis and truncate:
				points.append(self._truncate(x,y))
			else:
				points.append((x,y))
		if ignore:
			return None
		return points
	
	def project(self, lat, lon):
		assert False, 'Proj is an abstract class'
				
	def _visible(self, lat, lon):
		assert False, 'Proj is an abstract class'
		
	def _truncate(self, x, y):
		assert False, 'truncation is not implemented'
	
	def __str__(self):
		return 'Proj('+name+')'
		

class Azimuthal(Proj):

	def __init__(self, lat0=0.0, lon0=0.0):
		self.lat0 = lat0
		self.lon0 = lon0
		self.elevation0 = self.to_elevation(lat0)
		self.azimuth0 = self.to_azimuth(lon0)

	def to_elevation(self,latitude):
		return ((latitude + 90.0) / 180.0) * math.pi - math.pi/2
	
	def to_azimuth(self,longitude):
		return ((longitude + 180.0) / 360.0) * math.pi*2 - math.pi

	def _visible(self, lat, lon):
		elevation = self.to_elevation(lat)
		azimuth = self.to_azimuth(lon)   
		# work out if the point is visible
		cosc = math.sin(elevation)*math.sin(self.elevation0)+math.cos(self.elevation0)*math.cos(elevation)*math.cos(azimuth-self.azimuth0)
		return cosc >= 0.0		


class Orthographic(Azimuthal):
	"""
	Orthographic Azimuthal Projection
	
	implementation taken from http://www.mccarroll.net/snippets/svgworld/
	"""
	def __init__(self,lat0,lon0,r):
		self.r = r
		Proj.__init__(self, 'ortho')
		Azimuthal.__init__(self, lat0, lon0)		

	"""
	def plot(self,region,truncate=True):
		points = []
		ignore = True
		for (latitude,longitude) in region:
			elevation = self.to_elevation(latitude)
			azimuth = self.to_azimuth(longitude)
		   
			# work out if the point is visible
			cosc = math.sin(elevation)*math.sin(self.elevation0)+math.cos(self.elevation0)*math.cos(elevation)*math.cos(azimuth-self.azimuth0)
			if cosc >= 0.0:
				# this point is visible, so do not ignore this region
				ignore = False
			# orthographic projection
			xo = self.r*math.cos(elevation)*math.sin(azimuth-self.azimuth0)
			yo = -self.r*(math.cos(self.elevation0)*math.sin(elevation)-math.sin(self.elevation0)*math.cos(elevation)*math.cos(azimuth-self.azimuth0))
			x = self.r + xo
			y = self.r + yo
			if cosc < 0:
				if not truncate: continue
				# this point is on the far side of the globe.  Truncate it to lie on the rim.
				theta = math.atan2(yo,xo)
				x1 = self.r + self.r * math.cos(theta)
				y1 = self.r + self.r * math.sin(theta)
				points.append((x1,y1))
			else:
				points.append((x,y))
		if ignore:
			return None
		return points
	"""	
	def project(self, lat, lon):
		elevation = self.to_elevation(latitude)
		azimuth = self.to_azimuth(longitude)
		xo = self.r*math.cos(elevation)*math.sin(azimuth-self.azimuth0)
		yo = -self.r*(math.cos(self.elevation0)*math.sin(elevation)-math.sin(self.elevation0)*math.cos(elevation)*math.cos(azimuth-self.azimuth0))
		x = self.r + xo
		y = self.r + yo
		
		return (x,y)

class LAEA(Azimuthal):
	"""
	Lambert Azimuthal Equal-Area Projection
	
	implementation taken from http://www.epsg.org/guides/G7-2.html
	"""
	def __init__(self,latitude0,longitude0):
		Proj.__init__(self, 'laea')
		Azimuthal.__init__(self, latitude0, longitude0)		
		
		from math import radians as rad, asin, pi
		
		_q = self._q
		self.a = a = self.earth_rad
		self.e = e = 0.081819191
		self.esq = e * e
		self.elO = elO = rad(latitude0)
		self.lamO = rad(longitude0)
		self.qP = qP = _q(pi*.5)
		self.qO = qO = _q(elO)
		self.Rq = a * pow(qP * .5, .5)
		self.betaO = asin(qO / qP)


	def _q(self, el):
		from math import log, sin, pow, radians as rad, pi as PI
		return (1-self.esq) * ( (sin(el) / (1 - self.esq * pow(sin(el),2))) - ( (1/(2*self.e)) * log((1 - self.e*sin(el)) / (1 + self.e*sin(el))) ))

	def project(self, lat, lon):
		from math import radians as rad, pow, asin, cos, sin
	
		el = rad(lat)
		lam = rad(lon)
		q = self._q(el)
		
		beta = asin(q/self.qP)
		
		D = self.a * (cos(self.elO) / pow(1- self.esq*pow(sin(self.elO),2) ,.5)) / ( self.Rq * cos(self.betaO) )
		
		B = self.Rq * pow( 2/( 1+sin(self.betaO)*sin(beta) + ( cos(self.betaO)*cos(beta)*cos(lam-self.lamO) ) ) , .5)
	
		FE = self.false_easting
		FN = self.false_northing
				
		x = FE + ((B*D) * (cos(beta)*sin(lam-self.lamO)))
		y = FN + (B/D) * ((cos(self.betaO)*sin(beta)) - (sin(self.betaO)*cos(beta)*cos(lam-self.lamO)))	
	
		return (x,y*-1)

class PlatteCarree(object):
	
	def project(self, lat, lon):
		return (lon, lat)
				
class Robinson(object):
	
	def __init__(self):
		import pyproj
		self.name = 'robin'
		self.proj = pyproj.Proj('+proj=robin')

	def project(self, lat, lon):
		x,y = self.proj(lon, lat)
		return (x,y)

class NaturalEarth(object):
	
	def __init__(self):
		from math import pi
		self.name = 'naturalearth'
		s = self
		s.A0 = 0.8707
		s.A1 = -0.131979
		s.A2 = -0.013791
		s.A3 = 0.003971
		s.A4 = -0.001529
		s.B0 = 1.007226
		s.B1 = 0.015085
		s.B2 = -0.044475
		s.B3 = 0.028874
		s.B4 = -0.005916
		s.C0 = s.B0
		s.C1 = 3 * s.B1
		s.C2 = 7 * s.B2
		s.C3 = 9 * s.B3
		s.C4 = 11 * s.B4
		s.EPS = 1e-11
		s.MAX_Y = 0.8707 * 0.52 * pi
		
	def project(self, lat, lon):
		from math import radians as rad
		lplam = rad(lon)
		lpphi = rad(lat*-1)
		phi2 = lpphi * lpphi
		phi4 = phi2 * phi2
		
		x = self.false_easting + lplam * (self.A0 + phi2 * (self.A1 + phi2 * (self.A2 + phi4 * phi2 * (self.A3 + phi2 * self.A4)))) * 1000
		y = self.false_northing + lpphi * (self.B0 + phi2 * (self.B1 + phi4 * (self.B2 + self.B3 * phi2 + self.B4 * phi4))) * 1000
		
		return (x,y)

	def plot(self,region, truncate=False):
		points = []
		
		for (lat,lon) in region:
			points.append(self.project(lat, lon))
			
		return points
		
		
if __name__ == '__main__':
	# some class testing
	p = LAEA(52.0,10.0)
	x,y = p.project(50,5)
	assert (round(x,2),round(y,2)) == (3962799.45, -2999718.85), 'LAEA proj error'
	
	p = NaturalEarth()
	