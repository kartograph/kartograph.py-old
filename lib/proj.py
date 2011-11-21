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

Most of the projection formulas are taken from PROJ.4 implementation

"""
import math 
from math import radians as rad

projections = dict()

class Proj(object):
	"""
	base class for projections
	"""	
	HALFPI = math.pi * .5
	QUARTERPI = math.pi * .25
					
	def plot(self, polygon, truncate=True):
		points = []
		ignore = True
		for (lon,lat) in polygon:
			vis = self._visible(lon, lat)
			if vis:
				ignore = False
			x,y = self.project(lon, lat)
			if not vis and truncate:
				points.append(self._truncate(x,y))
			else:
				points.append((x,y))
		if ignore:
			return None
		return [points]
	
	def project(self, lon, lat):
		assert False, 'Proj is an abstract class'
				
	def _visible(self, lon, lat):
		assert False, 'Proj is an abstract class'
	
	def _truncate(self, x, y):
		assert False, 'truncation is not implemented'
	
	def world_bounds(self):
		assert False, 'world_bounds not implemented'
	
	def sea_shape(self):
		assert False, 'sea_shape not implemented'
	
	def __str__(self):
		return 'Proj('+self.name+')'
		
	def toXML(self):
		from svgfig import SVG
		p = SVG('proj', id=self.name)
		return p
	
	@staticmethod
	def fromXML(xml):
		id = xml['id']
		if id in projections:
			ProjClass = projections[id]
			args = {}
			for (prop,val) in xml:
				if prop[0] != "id":
					args[prop[0]] = float(val)
			return ProjClass(**args)
		raise Exception("could not restore projection from xml")
		
		
class Cylindrical(Proj):

	def __init__(self, lon0 = 0.0):
		self.lon0 = lon0
		
		sea = []
		for lat in range(-90,90): sea.append((-180,lat))
		for lon in range(-180,180): sea.append((lon, 90))
		for lat in range(-90,90): sea.append((180,lat*-1))
		for lon in range(-180,180): sea.append((lon*-1, -90))
		self.sea = sea
		
		if lon0 != 0.0:
			from Polygon import Polygon as Poly 
			self.inside_p = Poly(sea)
			
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

	def _visible(self, lon, lat):
		return True	
		
	def _truncate(self, x, y):
		return (x,y)
		
	def world_bounds(self):
		from gisutils import Bounds2D, Point
		bbox = Bounds2D()
		for lat,lon in [(0,-180),(0,180),(-90,0),(90,0)]:
			x,y = self.project(lon, lat)
			bbox.update(Point(x,y))
		return bbox
	
	def sea_shape(self):
		sea = []
		out = []
		for lat in range(-90,90): sea.append((-180,lat))
		for lon in range(-180,180): sea.append((lon, 90))
		for lat in range(-90,90): sea.append((180,lat*-1))
		for lon in range(-180,180): sea.append((lon*-1, -90))
		for s in sea:
			lon, lat = s
			out.append(self.project(lon, lat))
		return out
		
	def toXML(self):
		p = super(Cylindrical, self).toXML()
		p['lon0'] = str(self.lon0)
		return p
		
	def __str__(self):
		return 'Proj('+self.name+', lon0=%s)' % self.lon0


class Equirectangular(Cylindrical):
	"""
	Equirectangular Projection, aka lonlat, aka plate carree
	"""
	def __init__(self, lon0 = 0.0, lat0 = 0.0):
		self.lat0 = lat0
		self.phi0 = rad(lat0 * -1)
		Cylindrical.__init__(self, lon0 = lon0)
	
	def project(self, lon, lat):
		return (lon * math.cos(self.phi0), lat*-1)

projections['lonlat'] = Equirectangular


class CEA(Cylindrical):
	"""
	Cylindrical Equal Area Projection
	"""
	def __init__(self, lat0 = 0.0, lon0 = 0.0):
		self.lat0 = lat0
		self.phi0 = rad(lat0 * -1)
		self.lam0 = rad(lon0)
		Cylindrical.__init__(self, lon0 = lon0)
		
	def project(self, lon, lat):
		lam = rad(lon)
		phi = rad(lat*-1)
		x = (lam) * math.cos(self.phi0)
		y = math.sin(phi) / math.cos(self.phi0)
		return (x,y)

projections['cea'] = CEA


class GallPeters(CEA):
	def __init__(self, lat0 = 0.0, lon0=0.0):
		CEA.__init__(self, lat0=45, lon0=lon0)

projections['gallpeters'] = GallPeters


class HoboDyer(CEA):
	def __init__(self, lat0=0.0, lon0=0.0):
		CEA.__init__(self, lat0=37.5, lon0=lon0)

projections['hobodyer'] = HoboDyer


class Behrmann(CEA):
	def __init__(self, lat0 = 0.0, lon0=0.0):
		CEA.__init__(self, lat0=30, lon0=lon0)

projections['behrmann'] = Behrmann


class Balthasart(CEA):
	def __init__(self, lat0 = 0.0, lon0=0.0):
		CEA.__init__(self, lat0=50, lon0=lon0)

projections['balthasart'] = Balthasart


class PseudoCylindrical(Cylindrical):
	def __init__(self, lon0=0.0):
		Cylindrical.__init__(self, lon0=lon0)




class NaturalEarth(PseudoCylindrical):
	
	def __init__(self, lat0=0.0, lon0=0.0):
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
		
	def project(self, lon, lat):
		from math import radians as rad
		lplam = rad(lon)
		lpphi = rad(lat*-1)
		phi2 = lpphi * lpphi
		phi4 = phi2 * phi2
		x = lplam * (self.A0 + phi2 * (self.A1 + phi2 * (self.A2 + phi4 * phi2 * (self.A3 + phi2 * self.A4)))) * 180 + 500
		y = lpphi * (self.B0 + phi2 * (self.B1 + phi4 * (self.B2 + self.B3 * phi2 + self.B4 * phi4))) * 180 + 270
		return (x,y)

projections['naturalearth'] = NaturalEarth
	
	
class Robinson(PseudoCylindrical):

	def __init__(self, lat0 = 0.0, lon0=0.0):
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

	def project(self, lon, lat):
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

projections['robinson'] = Robinson


class EckertIV(PseudoCylindrical):

	def __init__(self, lon0=0.0, lat0=0):
		PseudoCylindrical.__init__(self, lon0=lon0)
	
		self.C_x = .42223820031577120149
		self.C_y = 1.32650042817700232218
		self.RC_y = .75386330736002178205
		self.C_p = 3.57079632679489661922
		self.RC_p = .28004957675577868795
		self.EPS = 1e-7
		self.NITER = 6
	
	def project(self, lon, lat):
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

projections['eckert4'] = EckertIV

		
class Sinusoidal(PseudoCylindrical):

	def __init__(self, lon0=0.0, lat0=0.0):
		PseudoCylindrical.__init__(self, lon0=lon0)
		
	def project(self, lon, lat):
		lam = rad(lon)
		phi = rad(lat*-1)
		x = lam * math.cos(phi)
		y = phi
		return (x,y)

projections['sinusoidal'] = Sinusoidal
	
	
class Mollweide(PseudoCylindrical):

	def __init__(self, p=1.5707963267948966, lon0=0.0, lat0=0.0, cx=None, cy=None, cp=None):
		PseudoCylindrical.__init__(self, lon0=lon0)
		self.MAX_ITER = 10
		self.TOLERANCE = 1e-7
		
		if p != None:
			p2 = p + p
			sp = math.sin(p)
			r = math.sqrt(math.pi*2.0 * sp / (p2 + math.sin(p2)))
			self.cx = 2. * r / math.pi
			self.cy = r / sp
			self.cp = p2 + math.sin(p2)
		elif cx != None and cy != None and cz != None:
			self.cx = cx
			self.cy = cy
			self.cp = cp
		else:
			assert False, 'either p or cx,cy,cp must be defined'
		
	def project(self, lon, lat):
		lam = rad(lon)
		phi = rad(lat)
		
		k = self.cp * math.sin(phi)
		i = self.MAX_ITER
		while i != 0:
			v = (phi + math.sin(phi) - k) / (1. + math.cos(phi))
			phi -= v
			if abs(v) < self.TOLERANCE:
				break;
			i -= 1
		
		if i == 0:
			phi = (self.HALFPI,-self.HALFPI)[phi < 0]
		else:
			phi *= 0.5
		
		x = self.cx * lam * math.cos(phi)
		y = self.cy * math.sin(phi)
		return (x,y*-1)

projections['mollweide'] = Mollweide
	
	
class WagnerIV(Mollweide):
	def __init__(self, lon0=0, lat0=0):
		# p=math.pi/3
		Mollweide.__init__(self, p=1.0471975511965976)

projections['wagner4'] = WagnerIV

		
class WagnerV(Mollweide):
	def __init__(self, lat0=0, lon0=0):
		Mollweide.__init__(self, cx = 0.90977, cy = 1.65014, cp = 3.00896)

projections['wagner5'] = WagnerV




class Azimuthal(Proj):

	def __init__(self, lat0=0.0, lon0=0.0, rad=1000):
		self.lat0 = lat0
		self.phi0 = math.radians(lat0)
		self.lon0 = lon0
		self.lam0 = math.radians(lon0)
		self.r = rad
		self.elevation0 = self.to_elevation(lat0)
		self.azimuth0 = self.to_azimuth(lon0)

	def to_elevation(self,latitude):
		return ((latitude + 90.0) / 180.0) * math.pi - math.pi/2
	
	def to_azimuth(self,longitude):
		return ((longitude + 180.0) / 360.0) * math.pi*2 - math.pi

	def _visible(self, lon, lat):
		elevation = self.to_elevation(lat)
		azimuth = self.to_azimuth(lon)   
		# work out if the point is visible
		cosc = math.sin(elevation)*math.sin(self.elevation0)+math.cos(self.elevation0)*math.cos(elevation)*math.cos(azimuth-self.azimuth0)
		return cosc >= 0.0		
		
	def _truncate(self, x, y):
		theta = math.atan2(y-self.r,x-self.r)
		x1 = self.r + self.r * math.cos(theta)
		y1 = self.r + self.r * math.sin(theta)
		return (x1,y1)
		
	def world_bounds(self):
		from gisutils import Bounds2D
		bbox = Bounds2D(width=self.r*2, height=self.r*2)
		return bbox
		
	def sea_shape(self):
		out = []
		for phi in range(0,360):
			x = self.r + math.cos(math.radians(phi)) * self.r
			y = self.r + math.sin(math.radians(phi)) * self.r
			out.append((x,y))
		return out
		
	def toXML(self):
		p = super(Azimuthal, self).toXML()
		p['lon0'] = str(self.lon0)
		p['lat0'] = str(self.lat0)
		return p
		
	def __str__(self):
		return 'Proj('+self.name+', lon0=%s, lat0=%s)' % (self.lon0, self.lat0)

	
		
class Conic(Proj):
	def __init__(self, lat0=0, lon0=0, lat1=0, lat2=0):
		from math import radians as rad
		self.lat0 = lat0
		self.phi0 = rad(lat0)
		self.lon0 = lon0
		self.lam0 = rad(lon0)
		self.lat1 = lat1
		self.phi1 = rad(lat1)
		self.lat2 = lat2
		self.phi2 = rad(lat2)
		
	def _visible(self, lon, lat):
		return (self.lat0 >= 0 and lat >= 0) or (self.lat0 < 0 and lat < 0)
		
	def _truncate(self, x, y):
		return (x,y)
		
	def world_bounds(self):
		from gisutils import Bounds2D, Point
		bbox = Bounds2D()
		for (x,y) in self.sea_shape():
			bbox.update(Point(x,y))
		return bbox
		
	def sea_shape(self):
		sea = []
		out = []
		for lat in range(-90,90): sea.append((self.lon0-180,lat))
		for lon in range(-180,180): sea.append((self.lon0+lon, 90))
		for lat in range(-90,90): sea.append((self.lon0+180,lat*-1))
		for lon in range(-180,180): sea.append((self.lon0 - lon, -90))
		for s in sea:
			lon, lat = s
			out.append(self.project(lon, lat))
		return out

	def toXML(self):
		p = super(Conic, self).toXML()
		p['lon0'] = str(self.lon0)
		p['lat0'] = str(self.lat0)
		p['lat1'] = str(self.lat1)
		p['lat2'] = str(self.lat2)
		return p

class Orthographic(Azimuthal):
	"""
	Orthographic Azimuthal Projection
	
	implementation taken from http://www.mccarroll.net/snippets/svgworld/
	"""
	def __init__(self,lat0=0,lon0=0):
		self.r = 1000
		Azimuthal.__init__(self, lat0, lon0)		

	def project(self, lon, lat):
		elevation = self.to_elevation(lat)
		azimuth = self.to_azimuth(lon)
		xo = self.r*math.cos(elevation)*math.sin(azimuth-self.azimuth0)
		yo = -self.r*(math.cos(self.elevation0)*math.sin(elevation)-math.sin(self.elevation0)*math.cos(elevation)*math.cos(azimuth-self.azimuth0))
		x = self.r + xo
		y = self.r + yo
		return (x,y)
		
projections['ortho'] = Orthographic


class LAEA(Azimuthal):
	"""
	Lambert Azimuthal Equal-Area Projection
	
	implementation taken from 
	Snyder, Map projections - A working manual
	"""
	def __init__(self,lon0=0.0,lat0=0.0):
		import sys
		self.scale = math.sqrt(2)*0.5
		Azimuthal.__init__(self, lat0, lon0)		
		
	def project(self, lon, lat):
		from math import radians as rad, pow, asin, cos, sin
		
		phi = rad(lat)
		lam = rad(lon)
		
		if False and abs(lon - self.lon0) == 180:
			xo = self.r*2
			yo = 0
		else:
			k = pow(2 / (1 + sin(self.phi0) * sin(phi) + cos(self.phi0)*cos(phi)*cos(lam - self.lam0)), .5)
			k *= self.scale#.70738033
				
			xo = self.r * k * cos(phi) * sin(lam - self.lam0)
			yo = -self.r * k * ( cos(self.phi0)*sin(phi) - sin(self.phi0)*cos(phi)*cos(lam - self.lam0) )
		
		x = self.r + xo
		y = self.r + yo
		
		return (x,y)

projections['laea'] = LAEA
	

class Stereographic(Azimuthal):
	"""
	Stereographic projection
	
	implementation taken from 
	Snyder, Map projections - A working manual
	"""
	def __init__(self,lat0=0.0,lon0=0.0):
		Azimuthal.__init__(self, lat0, lon0)		
		
	def project(self, lon, lat):
		from math import radians as rad, pow, asin, cos, sin
		
		phi = rad(lat)
		lam = rad(lon)

		k0 = 0.5
		k = 2*k0 / (1 + sin(self.phi0) * sin(phi) + cos(self.phi0)*cos(phi)*cos(lam - self.lam0))
		
		xo = self.r * k * cos(phi) * sin(lam - self.lam0)
		yo = -self.r * k * ( cos(self.phi0)*sin(phi) - sin(self.phi0)*cos(phi)*cos(lam - self.lam0) )
		
		x = self.r + xo
		y = self.r + yo
		
		return (x,y)

projections['stereo'] = Stereographic


class Satellite(Azimuthal):
	"""
	General perspective projection, aka Satellite projection
	
	implementation taken from 
	Snyder, Map projections - A working manual
	
	up .. angle the camera is turned away from north (clockwise)
	tilt .. angle the camera is tilted 
	"""
	def __init__(self,lat0=0.0,lon0=0.0,dist=1.6,up=0, tilt=0):
		import sys
		Azimuthal.__init__(self, 0, 0)
		
		self.dist = dist
		self.up = up
		self.up_ = math.radians(up)
		self.tilt = math.radians(tilt)
		
		self.scale = 1
		xmin = sys.maxint
		xmax = sys.maxint*-1
		for lat in range(0,180):
			for lon in range(0,361):
				x,y = self.project(lon-180,lat-90)
				xmin = min(x, xmin)
				xmax = max(x, xmax)
		self.scale = (self.r*2)/(xmax-xmin) 
		
		Azimuthal.__init__(self, lat0, lon0)
		
		
	def project(self, lon, lat):
		from math import radians as rad, pow, asin, cos, sin
		
		phi = rad(lat)
		lam = rad(lon)

		cos_c = sin(self.phi0) * sin(phi) + cos(self.phi0) * cos(phi) * cos(lam - self.lam0)
		k = (self.dist - 1) / (self.dist - cos_c)
		k = (self.dist - 1) / (self.dist - cos_c)
		
		k *= self.scale
		
		xo = self.r * k * cos(phi) * sin(lam - self.lam0)
		yo = -self.r * k * ( cos(self.phi0)*sin(phi) - sin(self.phi0)*cos(phi)*cos(lam - self.lam0) )
		
		# rotate
		cos_up = cos(self.up_)
		sin_up = sin(self.up_)
		cos_tilt = cos(self.tilt)
		sin_tilt = sin(self.tilt)
		
		H = self.r * (self.dist - 1)
		A = ((yo * cos_up + xo * sin_up) * sin(self.tilt/H)) + cos_tilt
		xt = (xo * cos_up - yo * sin_up) * cos(self.tilt/A)
		yt = (yo * cos_up + xo * sin_up) / A
		
		x = self.r + xt
		y = self.r + yt	
		
		return (x,y)	

	def _visible(self, lon, lat):
		elevation = self.to_elevation(lat)
		azimuth = self.to_azimuth(lon)   
		# work out if the point is visible
		cosc = math.sin(elevation)*math.sin(self.elevation0)+math.cos(self.elevation0)*math.cos(elevation)*math.cos(azimuth-self.azimuth0)
		return cosc >= (1.0/self.dist)
	
	def toXML(self):
		p = super(Satellite, self).toXML()
		p['dist'] = str(self.dist)
		p['up'] = str(self.up)
		return p

projections['satellite'] = Satellite


class LCC(Conic):
	"""
	Lambert Conformal Conic Projection (spherical)
	"""
	def __init__(self, lat0=0, lon0=0, lat1=30, lat2=50):
		from math import sin,cos,tan,pow,log
		Conic.__init__(self, lat0=lat0, lon0=lon0, lat1=lat1, lat2=lat2)	
		self.n = n = sinphi = sin(self.phi1)
		cosphi = cos(self.phi1)
		secant = abs(self.phi1 - self.phi2) >= 1e-10
		
		if secant:
			n = log(cosphi / cos(self.phi2)) / log(tan(self.QUARTERPI + .5 * self.phi2) / tan(self.QUARTERPI + .5 * self.phi1))
		self.c = c = cosphi * pow(tan(self.QUARTERPI + .5 * self.phi1), n) / n
		if abs(abs(self.phi0) - self.HALFPI) < 1e-10:
			self.rho0 = 0.
		else:
			self.rho0 = c * pow(tan(self.QUARTERPI + .5 * self.phi0), -n)
		
	def project(self, lon, lat):
		phi = rad(lat)
		lam = rad(lon)
		n = self.n		
		if abs(abs(phi) - self.HALFPI) < 1e-10:
			rho = 0.0
		else:
			rho = self.c * math.pow(math.tan(self.QUARTERPI + 0.5 * phi), -n)
		lam_ = (lam - self.lam0) * n
		x = rho * math.sin(lam_)
		y = self.rho0 - rho * math.cos(lam_)
		
		return (x,y*-1)
		
projections['lcc'] = LCC

			
class Proj4(Proj):
	
	def __init__(self, projstr):
		import pyproj
		self.proj = pyproj.Proj(projstr)
		
	def project(self, lon, lat):
		x,y = self.proj(lon, lat)
		return (x,y*-1)


class LCC__(Proj4):
	
	def __init__(self, lat0=0, lon0=0, lat1=28, lat2=30):
		Proj4.__init__(self, '+proj=lcc +lat_0=%f +lon_0=%f +lat_1=%f +lat_2=%f' % (lat0, lon0, lat1, lat2))
		
	def _visible(self, lon, lat):
		return True
		
	def _truncate(self, x,y):
		return (x,y)

		

		
		
	

			


	



for pjname in projections:
	projections[pjname].name = pjname
		
if __name__ == '__main__':
	import sys
	# some class testing
	#p = LAEA(52.0,10.0)
	#x,y = p.project(50,5)
	#assert (round(x,2),round(y,2)) == (3962799.45, -2999718.85), 'LAEA proj error'
	
	print Proj.fromXML(Robinson(lat0=3, lon0=4).toXML())
	
	Robinson(lat0=3, lon0=4)
	
	for pj in projections:
		Proj = projections[pj]
		try:
			proj = Proj(lat0=34.0, lon0=60)
			proj.project(0,0)
			proj.world_bounds()
			print proj.toXML()
		except:
			print 'Error', pj
			print sys.exc_info()[0]
			raise