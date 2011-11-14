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
from math import radians as rad

__known_projections__ = ('ortho', 'laea', 'naturalearth', 'cea', 'gallpeters', 'hobodyer', 'behrmann', 'balthasart')

class Proj(object):
	"""
	base class for projections
	"""
	def __init__(self):
		self.azimuthal = False
		self.earth_rad = 6378137.0
		self.false_easting = 4321000.00
		self.false_northing = 3210000.00
		
	def plot(self, polygon, truncate=True):
		points = []
		ignore = True
		for (lon,lat) in polygon:
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
		return [points]
	
	def project(self, lat, lon):
		assert False, 'Proj is an abstract class'
				
	def _visible(self, lat, lon):
		assert False, 'Proj is an abstract class'
	
	def _truncate(self, x, y):
		assert False, 'truncation is not implemented'
	
	def __str__(self):
		return 'Proj('+name+')'
		

class Azimuthal(Proj):

	def __init__(self, lat0=0.0, lon0=0.0, rad=1000):
		self.lat0 = lat0
		self.lon0 = lon0
		self.r = rad
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
		
	def _truncate(self, x, y):
		theta = math.atan2(y,x)
		x1 = self.r + self.r * math.cos(theta)
		y1 = self.r + self.r * math.sin(theta)


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
		
		# x = self.false_easting + ...
		
		return (x,y)

class LAEA(Azimuthal):
	"""
	Lambert Azimuthal Equal-Area Projection
	
	implementation taken from http://www.epsg.org/guides/G7-2.html
	"""
	def __init__(self,lat0=0.0,lon0=0.0):
		Proj.__init__(self)
		Azimuthal.__init__(self, lat0, lon0, rad=self.earth_rad)		
		
		from math import radians as rad, asin, pi
		
		_q = self._q
		self.a = a = self.earth_rad
		self.e = e = 0.081819191
		self.esq = e * e
		self.elO = elO = rad(lat0)
		self.lamO = rad(lon0)
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
				
class Proj4(Proj):
	
	def __init__(self, name, projstr):
		import pyproj
		self.name = name
		self.proj = pyproj.Proj(projstr)
		
	def project(self, lat, lon):
		x,y = self.proj(lon, lat*-1)
		return (x,y)





class Cylindrical(Proj):

	def __init__(self, lon0 = 0.0):
		self.lon0 = lon0
		if lon0 != 0.0:
			from Polygon import Polygon as Poly 
			inside_pts = []
			for lat in range(-90,90): inside_pts.append((-180,lat))
			for lon in range(-180,180): inside_pts.append((lon, 90))
			for lat in range(-90,90): inside_pts.append((180,lat*-1))
			for lon in range(-180,180): inside_pts.append((lon*-1, -90))
			self.inside_p = Poly(inside_pts)
			
	def plot(self, polygon, truncate=True):
		if self.lon0 != 0.0:
			
			polygons = self._shift_polygon(polygon)
			
			plotted = []
			for polygon in polygons:
				plotted += super(Cylindrical, self).plot(polygon, False)
			return plotted
		else:
			return super(Cylindrical, self).plot(polygon, False)

	def _shift_polygon(self, polygon):
		"""
		shifts a polygon according to the origin longitude
		"""
		from Polygon import Polygon as Poly 
		# we need to split and join some polygons
		poly_coords = []
		for (lon,lat) in polygon:
			poly_coords.append((lon-self.lon0,lat))
		poly = Poly(poly_coords)
		
		polygons = []
		
		p_in = poly & self.inside_p
		for i in range(len(p_in)):
			polygon = []
			for (lon,lat) in p_in.contour(i):
				polygon.append((lon,lat))
			polygons.append(polygon)
		
		p_out = poly - p_in
		for i in range(len(p_out)):
			polygon = []
			s = 0
			c = 0
			for (lon,lat) in p_out.contour(i):
				s += lon
				c += 1
			left = s/float(c) < -180 # check avg longitude
			for (lon,lat) in p_out.contour(i):
				polygon.append((lon+(-360,360)[left],lat))
			polygons.append(polygon)
		return polygons

	def _visible(self, lat, lon):
		return True	
		
	def _truncate(self, x, y):
		return (x,y)
	
	
class CEA(Cylindrical):
	def __init__(self, lat0 = 0.0, lon0 = 0.0):
		self.lat0 = lat0
		self.lon0 = lon0
		self.phi0 = rad(lat0 * -1)
		self.lam0 = rad(lon0)
		Proj.__init__(self)
		Cylindrical.__init__(self, lon0 = lon0)
		
	def project(self, lat, lon):
		lam = rad(lon)
		phi = rad(lat*-1)
		x = (lam) * math.cos(self.phi0)
		y = math.sin(phi) / math.cos(self.phi0)
		return (x,y)
			

class GallPeters(CEA):
	def __init__(self, lon0=0.0):
		CEA.__init__(self, lat0=45, lon0=lon0)

class HoboDyer(CEA):
	def __init__(self, lon0=0.0):
		CEA.__init__(self, lat0=37.5, lon0=lon0)

class Behrmann(CEA):
	def __init__(self, lon0=0.0):
		CEA.__init__(self, lat0=30, lon0=lon0)
	
class Balthasart(CEA):
	def __init__(self, lon0=0.0):
		CEA.__init__(self, lat0=50, lon0=lon0)
	

class PseudoCylindrical(Cylindrical):
	def __init__(self, lon0=0.0):
		Cylindrical.__init__(self, lon0=lon0)


class NaturalEarth(PseudoCylindrical):
	
	def __init__(self, lon0=0.0):
		PseudoCylindrical.__init__(self, lon0=lon0)
		from math import pi
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
		x = lplam * (self.A0 + phi2 * (self.A1 + phi2 * (self.A2 + phi4 * phi2 * (self.A3 + phi2 * self.A4)))) * 1000
		y = lpphi * (self.B0 + phi2 * (self.B1 + phi4 * (self.B2 + self.B3 * phi2 + self.B4 * phi4))) * 1000
		return (x,y)
	
	
class Robinson(PseudoCylindrical):

	def __init__(self, lon0=0.0):
		PseudoCylindrical.__init__(self, lon0=lon0)
		self.X = [1, -5.67239e-12, -7.15511e-05, 3.11028e-06,  0.9986, -0.000482241, -2.4897e-05, -1.33094e-06, 0.9954, -0.000831031, -4.4861e-05, -9.86588e-07, 0.99, -0.00135363, -5.96598e-05, 3.67749e-06, 0.9822, -0.00167442, -4.4975e-06, -5.72394e-06, 0.973, -0.00214869, -9.03565e-05, 1.88767e-08, 0.96, -0.00305084, -9.00732e-05, 1.64869e-06, 0.9427, -0.00382792, -6.53428e-05, -2.61493e-06, 0.9216, -0.00467747, -0.000104566, 4.8122e-06, 0.8962, -0.00536222, -3.23834e-05, -5.43445e-06, 0.8679, -0.00609364, -0.0001139, 3.32521e-06, 0.835, -0.00698325, -6.40219e-05, 9.34582e-07, 0.7986, -0.00755337, -5.00038e-05, 9.35532e-07, 0.7597, -0.00798325, -3.59716e-05, -2.27604e-06, 0.7186, -0.00851366, -7.0112e-05, -8.63072e-06, 0.6732, -0.00986209, -0.000199572, 1.91978e-05, 0.6213, -0.010418, 8.83948e-05, 6.24031e-06, 0.5722, -0.00906601, 0.000181999, 6.24033e-06, 0.5322,  0.,  0.,  0.]
		self.Y = [0, 0.0124, 3.72529e-10, 1.15484e-09, 0.062, 0.0124001, 1.76951e-08, -5.92321e-09, 0.124, 0.0123998, -7.09668e-08, 2.25753e-08, 0.186, 0.0124008, 2.66917e-07, -8.44523e-08, 0.248, 0.0123971, -9.99682e-07, 3.15569e-07, 0.31, 0.0124108, 3.73349e-06, -1.1779e-06, 0.372, 0.0123598, -1.3935e-05, 4.39588e-06, 0.434, 0.0125501, 5.20034e-05, -1.00051e-05, 0.4968, 0.0123198, -9.80735e-05, 9.22397e-06, 0.5571, 0.0120308, 4.02857e-05, -5.2901e-06, 0.6176, 0.0120369, -3.90662e-05, 7.36117e-07, 0.6769, 0.0117015, -2.80246e-05, -8.54283e-07, 0.7346, 0.0113572, -4.08389e-05, -5.18524e-07, 0.7903, 0.0109099, -4.86169e-05, -1.0718e-06, 0.8435, 0.0103433, -6.46934e-05, 5.36384e-09, 0.8936, 0.00969679, -6.46129e-05, -8.54894e-06, 0.9394, 0.00840949, -0.000192847, -4.21023e-06, 0.9761, 0.00616525, -0.000256001, -4.21021e-06, 1.,  0.,  0.,  0]
		self.NODES = 18
		self.FXC = 0.8487
		self.FYC = 1.3523
		self.C1 = 11.45915590261646417544
		self.RC1 = 0.08726646259971647884
		self.ONEEPS = 1.000001
		self.EPS = 1e-8

	def _poly(self, arr, off, z):
		return arr[off]+z * (arr[off+1]+z * (arr[off+2]+z * (arr[off+3])))

	def project(self, lat, lon):
		lplam = rad(lon)
		lpphi = rad(lat*-1)

		phi = abs(lpphi)
		i = int(phi * self.C1)
		if i >= self.NODES:
			i = self.NODES - 1
		phi = math.degrees(phi - self.RC1 * i)
		i *= 4
		x = self._poly(self.X, i, phi) * self.FXC * lplam;
		y = self._poly(self.Y, i, phi) * self.FYC;
		if lpphi < 0.0:
			y = -y
			
		return (x,y)


class EckertIV(PseudoCylindrical):

	def __init__(self, lon0=0.0):
		PseudoCylindrical.__init__(self, lon0=lon0)
	
		self.C_x = .42223820031577120149
		self.C_y = 1.32650042817700232218
		self.RC_y = .75386330736002178205
		self.C_p = 3.57079632679489661922
		self.RC_p = .28004957675577868795
		self.EPS = 1e-7
		self.NITER = 6
	
	def project(self, lat, lon):
		lplam = rad(lon)
		lpphi = rad(lat*-1)
				
		p = self.C_p * math.sin(lpphi)
		V = lpphi * lpphi
		lpphi *= 0.895168 + V * ( 0.0218849 + V * 0.00826809 )
		
		i = self.NITER
		while i>0:
			c = math.cos(lpphi)
			s = math.sin(lpphi)
			V = (lpphi + s * (c + 2.) - p) / (1. + c * (c + 2.) - s * s)
			lpphi -= V
			if abs(V) < self.EPS:
				break
			i -= 1
		
		if i == 0:
			x = self.C_x * lplam
			y = (self.C_y, -self.C_y)[lpphi<0]
		else:
			x = self.C_x * lplam * (1. + math.cos(lpphi))
			y = self.C_y * math.sin(lpphi);
		return (x,y);
	

projections = dict()

projections['robinson'] = Robinson
projections['naturalearth'] = NaturalEarth
projections['laea'] = LAEA
projections['cea'] = CEA
projections['gallpeters'] = GallPeters
projections['hobodyer'] = HoboDyer
projections['behrmann'] = Behrmann
projections['balthasart'] = Balthasart
projections['eckert4'] = EckertIV

for pjname in projections:
	projections[pjname].name = pjname
		
if __name__ == '__main__':
	# some class testing
	p = LAEA(52.0,10.0)
	x,y = p.project(50,5)
	assert (round(x,2),round(y,2)) == (3962799.45, -2999718.85), 'LAEA proj error'
	
	p = NaturalEarth()
	