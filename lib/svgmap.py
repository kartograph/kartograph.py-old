#!/usr/bin/env python2.7
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

# exceptions for some countries

ignore = set('ATA')


"""
a list of exceptions for the country bbox computation
"""
country_min_area = {}
country_min_area['JPN'] = .1
country_min_area['AUS'] = .01
country_min_area['CAN'] = .05
country_min_area['ALA'] = .1
country_min_area['FRA'] = .2
country_min_area['DNK'] = .1
country_min_area['ITA'] = .05
country_min_area['GBR'] = .165
country_min_area['ESP'] = .165

"""
a list of exceptions for country center computation
"""
custom_country_center = {}
custom_country_center['USA'] = (-98.606,39.622)	
		
from gisutils import Bounds2D, Point, View, Polygon
import gisutils
import proj

class SVGMap:

	def __init__(self, options=None):
		self.options = options
		if self.options is None: 
			self.options = SVGMapOptions()
		
		self.options.applyDefaults()
		
		self.shp_src = {}
		self.shp_src['countries'] = self.options.data_path + 'shp/ne_10m_admin_0_countries'
		self.shp_src['regions'] = self.options.data_path + 'shp/ne_10m_admin_1_states_provinces_shp'
		self.shp_src['lakes'] = self.options.data_path + 'shp/ne_10m_lakes.shp'
		
		self.load_shape_records()
		

	def load_shape_records(self):
		"""
		loads the shapefile records (but not the shapes)
		"""
		import shapefile
		options = self.options

		# definition of shapefiles 		
		
		if options.verbose: print "loading shapefile records"
		
		self.sf_reader = sread = {} # shapefile reader
		self.sf_recs = srecs = {} # shapefile record
		self.sf_shapes = sshp = {} # shapefile shapes
		self.shp_area = sarea = {} # shape area cache
		
		for shpfile in self.shp_src:
			sread[shpfile] = shapefile.Reader(self.shp_src[shpfile]) # intantiate reader
			srecs[shpfile] = sread[shpfile].records() # load records
			sshp[shpfile] = [None]*len(srecs[shpfile]) # prepare shape cache
			sarea[shpfile] = [None]*len(srecs[shpfile]) # prepare shp area cache
			
		self.build_country_index() 
			

	def get_shape(self, sf, index):
		"""
		returns a shapefile shape, either from cache or from shapefile reader
		"""
		shp = self.sf_shapes[sf][index]
		if shp is None:
			shp = self.sf_shapes[sf][index] = self.sf_reader[sf].shapeRecord(index).shape
		return shp


	def build_country_index(self):
		"""
		creates a dict of iso3 -> index
		"""
		country_recs = self.sf_recs['countries']
		ci = {}
		for i in range(len(country_recs)):
			iso3 = country_recs[i][29]
			ci[iso3] = i
		self.country_index = ci
	
	
	def get_country_record(self, iso3):
		"""
		convenient wrapper around sf_recs and country_index
		"""
		if iso3 in self.country_index:
			index = self.country_index[iso3]
			return self.sf_recs['countries'][index]
		else:
			raise KeyError(iso3+' is no valid country-code')
			
	
	def get_country_shape(self, iso3):
		"""
		convenient wrapper around get_shape and country_index
		"""
		if iso3 in self.country_index:
			index = self.country_index[iso3]
			return self.get_shape('countries', index)
		else:
			raise KeyError(iso3+' is no valid country-code')
	
	
	def shape_area(self, sf, index):
		"""
		returns the area of a shape, either from cache or freshly computed
		"""
		if self.shp_area[sf][index] == None:
			# not in cache, so compute
			shp = self.get_shape(sf, index)
			self.shp_area[sf][index] = gisutils.shape_area(shp)
			
		return self.shp_area[sf][index]
		
	
	def get_country_region_indices(self, iso3):
		"""
		returns a list of region shape indices for a country
		"""
		region_recs = self.sf_recs['regions']
		reg_indices = []
		for i in range(len(region_recs)):
			if iso3 == region_recs[i][2]:
				reg_indices.append(i)
		return reg_indices
		
	
	def get_country_bbox(self, iso3, globe):
		""" 
		returns the projected bounding box for a countries largest polygons
		"""	
		min_area_percent = 0.2
		options = self.options
	
		if iso3 in country_min_area:
			# use value defined in exceptions
			min_area_percent = country_min_area[iso3]
	
		shape = self.get_country_shape(iso3)
		parts = shape.parts[:]
		parts.append(len(shape.points))
		max_area = 0
		areas = []
		for j in range(0,len(parts)-1):
			pts = shape.points[parts[j]:parts[j+1]]
			a = gisutils.area(pts)
			areas.append(a)
		max_area = max(areas)
		
		bbox = Bounds2D()
		
		kept = 0
		skipped = 0
		
		for j in range(0,len(parts)-1):
			pts = shape.points[parts[j]:parts[j+1]]
			if areas[j] >= max_area * min_area_percent:
				kept += 1
				lonlat = []
				for k in range(0,len(pts)):
					lonlat.append((pts[k][0], pts[k][1]))
				
				mpoints = globe.plot(lonlat)
				
				if mpoints == None: continue
				for points in mpoints:
					for xy in points:
						pt = Point(xy[0], xy[1])
						bbox.update(pt)
			else:
				skipped += 1
				if options.verbose:
					#print iso3,'skipping shape part',j,'because area is too small'
					#print iso3, min_area_percent, round(areas[j]), round(max_area)
					pass
		if options.verbose:
			print iso3, kept, 'shapes kept,', skipped,'shapes skipped'
		return bbox


	def get_region_rec(self, iso3, region):
		"""
		get bounding box for region
		focusRegion = (7,'DE.BW')
		"""
		shapes = self.get_country_region_indices(iso3)
		index,value = focusRegion
		for s in shapes:
			rec = self.sf_recs['regions'][s]
			if rec[index] == value:
				return rec
	
	
	def get_region_shape(self, iso3, region):
		"""
		get bounding box for region
		focusRegion = (7,'DE.BW')
		"""
		shapes = self.get_country_region_indices(iso3)
		index,value = region
		for s in shapes:
			rec = self.sf_recs['regions'][s]
			if rec[index] == value:
				return self.get_shape('regions', s)
				

	def get_region_bbox(self, iso3, globe, region):
		"""
		get bounding box for region
		focusRegion = (7,'DE.BW')
		"""
		
		shp = self.get_region_shape(iso3, region)
		parts = shp.parts[:]
		parts.append(len(shp.points))
		
		bbox = Bounds2D()
		for j in range(0,len(parts)-1):
			pts = shp.points[parts[j]:parts[j+1]]
			lonlat = []
			for k in range(0,len(pts)):
				lonlat.append((pts[k][0], pts[k][1]))
			mpoints = globe.plot(lonlat)
			
			for points in mpoints:
				for xy in points:
					pt = Point(xy[0], xy[1])
					bbox.update(pt)
		return bbox
	
	
	def get_region_center(self, iso3, globe):
		"""
		get bounding box for region
		focusRegion = (7,'DE.BW')
		"""
		
		shp = get_region_shape(iso3, region)
		bbox = Bounds2D()
		for j in range(0,len(parts)-1):
			pts = shape.points[parts[j]:parts[j+1]]
			lonlat = []
			for k in range(0,len(pts)):
				lonlat.append((pts[k][0], pts[k][1]))
			mpoints = globe.plot(lonlat)
			
			for points in mpoints:
				for xy in points:
					pt = Point(xy[0], xy[1])
					bbox.update(pt)
		return bbox
	

	def init_svg_canvas(self, view, bbox, globe):
		"""
		prepare a blank new svg file
		"""
		from svgfig import canvas, SVG
		
		options = self.options
		w = view.width
		h = view.height+2
		
		svg = canvas(width='%dpx' % w, height='%dpx' % h, viewBox='0 0 %d %d' % (w, h), enable_background='new 0 0 %d %d' % (w, h), style='stroke-width:0.7pt; stroke-linejoin: round; stroke:#444; fill:white;')
	
		css = 'path { fill-rule: evenodd; }\n#context path { fill: #eee; stroke: #bbb; } '
		
		if options.graticule:
			css += '#graticule path { fill: none; stroke-width:0.25pt;  } #graticule .equator { stroke-width: 0.5pt } '
	
		svg.append(SVG('defs', SVG('style', css, type='text/css')))
	
		meta = SVG('metadata')
		views = SVG('views')
		view = SVG('view', padding=str(options.out_padding), w=w, h=h)
		proj = globe.toXML()
		bbox = SVG('bbox', x=round(bbox.left,2), y=round(bbox.top,2), w=round(bbox.width,2), h=round(bbox.height,2))
		
		views.append(view)
		view.append(proj)
		view.append(bbox)
		
		meta.append(views)
		svg.append(meta)
		
		return svg


	def get_shape_polygons(self, shp, id, globe, view, data=None, holes=False):
		"""
		projects a shapefile shape and returns a list of polygons
		"""
		polys = []
		if shp.shapeType in (3,5):
			parts = shp.parts[:]
			parts.append(len(shp.points))
			if data is None: data = {}
			errs = 0
			for j in range(0,len(parts)-1):
				pts = shp.points[parts[j]:parts[j+1]]
				lonlat = []
				for k in range(0,len(pts)):
					lonlat.append((pts[k][0],pts[k][1]))
				
				
				mpoints = globe.plot(lonlat)
				if mpoints == None: continue
				for points in mpoints:
					poly_points = []
					for xy in points:
						if xy != None:
							poly_points.append(view.project(Point(xy[0], xy[1])))
						else: errs += 1
					polygon = Polygon(id, poly_points, mode='point', data=data, closed=shp.shapeType == 5, isHole=holes)
					if polygon != None:
						polys.append(polygon)
		else:
			print shp.shapeType
		return polys


	def get_polygon_data(self, rec, regions=False):
		if regions:
			data = { 'oid': rec[0], 'iso': rec[2] }
			if rec[7] != "":
				data['hasc'] = rec[7]
			if rec[19] != "":
				data['fips'] = rec[19][-2:]
			if rec[7] == "" and rec[19] == "":
				data['name'] =  Utils.remove_unicode(rec[4].decode('ISO 8859-1'))
		else:
			data = { 'iso': rec[29] }
		return data	
		

	def get_polygons_country(self, iso3, view, globe, regions=False):
		"""
		returns a list of polygons for a single country or it's regions
		used for mode=country and mode=regions without context
		"""
		options = self.options
		region_recs = self.sf_recs['regions']
		
		if regions:
			reg_indices = self.get_country_region_indices(iso3)
			polys = []
			for j in reg_indices:
				rec = region_recs[j]
				shp = self.get_shape('regions', j)
				clon,clat = gisutils.shape_center(shp)
				print '%s\t%f\t%f' % (rec[7],clon,clat)
				polys += self.get_shape_polygons(shp, iso3, globe, view, data=self.get_polygon_data(rec, regions=True))
		else:
			shp = self.get_country_shape(iso3)
			rec = self.get_country_record(iso3)
			polys = self.get_shape_polygons(shp, iso3, globe, view, data=self.get_polygon_data(rec))		
		return polys
	

	def get_polygons_country_context(self, country_iso3, viewbox, view, globe, regions=False):
		"""
		returns a list of polygons that are visible in the view
		used for mode=country and mode=regions with context
		"""
		polygons = []
		
		#options = self.options, country_recs, country_shapes, region_recs, region_sf
		options = self.options
		
		focus_shape = self.get_country_shape(country_iso3)
		focus_rec = self.get_country_record(country_iso3)
		
		country_recs = self.sf_recs['countries']
		region_recs = self.sf_recs['regions']
		
		if regions:
			reg_indices = self.get_country_region_indices(country_iso3)
		
		for i in range(len(country_recs)):
			iso3 = country_recs[i][29].upper()
			if iso3 != country_iso3:
				# this is not the center country	
				shp = self.get_shape('countries', i)
				polys = self.get_shape_polygons(shp, iso3, globe, view, data=self.get_polygon_data(country_recs[i]))
				
				for poly in polys:
					if poly.bbox.intersects(viewbox): # check if polygon intersects view
						polygons.append(poly)			
			
			else:
				# this is the center country
				if regions and len(reg_indices) > 0:
					# we have regions for this country
					for j in reg_indices:
						rec = region_recs[j]
						shp = self.get_shape('regions', j)
						polygons += self.get_shape_polygons(shp, iso3, globe, view, data=self.get_polygon_data(rec, regions=True))
				else:
					# we don't have or don't want regions, instead use the country itself
					polygons += self.get_shape_polygons(focus_shape, iso3, globe, view)
					
					if regions and options.verbose:
						print "..no available regions for ",iso3
		return polygons


	def get_polygons_world(self, globe, view):
		"""
		returns a list of gisutils.Polygon that will be visible in the map
		used for mode=world
		"""
		polygons = []
			
		country_recs = self.sf_recs['countries']
		
		for i in range(len(country_recs)):
			shp = self.get_shape('countries', i)
			iso3 = country_recs[i][29]
			polygons += self.get_shape_polygons(shp, iso3, globe, view, data=self.get_polygon_data(country_recs[i]))
		
		return polygons
	
	
	def get_polygons_countries(self, viewbox, view, globe, regions=False):
		"""
		returns a list of polygons that will be visible in the map
		used for mode=countries
		"""
		polygons = []
		country_recs = self.sf_recs['countries']
		for i in range(len(country_recs)):
			rec = country_recs[i]
			iso3 = rec[29].upper()
			shp = self.get_shape('countries', i)
			polys = self.get_shape_polygons(shp, iso3, globe, view, data=self.get_polygon_data(rec))
			
			for poly in polys:
				if poly.bbox.intersects(viewbox):
					polygons.append(poly)			
			
		return polygons



	def join_regions(self, iso3, polygons):
		"""
		at some exceptional cases, country regions need to be merged
		"""
		import csv
		options = self.options
		
		join_csv_src = options.data_path + 'region_joins.csv'
		join_data = csv.reader(open(join_csv_src), dialect='excel-tab')
		join_map = {} # objectid --> new region id
		
		for row in join_data:
			join_map[row[2]] = row[1]
			
		groups = {}
		out = []
		
		for poly in polygons:
			if 'oid' in poly.data and str(poly.data['oid']) in join_map:
				regId = join_map[str(poly.data['oid'])]
				if regId == '': regId = 'n/a'
				if regId not in groups:
					groups[regId] = []
				groups[regId].append(poly)
			else:
				out.append(poly)
		
		for gid in groups:
			polys = merge_polygons(groups[gid], id=iso3, data={ 'r-id': gid })
			for poly in polys:
				out.append(poly)		
				
		return out
		
	
	def simplify_polygons(self, polygons, focusFilter=None):
		"""
		simplifies or generalizes a list of polygons
		"""
		options = self.options
		
		if options.verbose: print "simplifying polygons"
		# join duplicate points
		
		gisutils.unify(polygons)
		simplify = gisutils.simplify
		
		if focusFilter != None:
			focus = []
			context = []
			for polygon in polygons:
				if focusFilter(polygon):
					focus.append(polygon)
				else:
					context.append(polygon)
					
			# simplify center country in the first pass	
			for polygon in focus:
				simplify(polygon, options.simplification)
			
			# simplify other countries in the snd pass
			for polygon in context:
				simplify(polygon, options.context_simplification)
		else:
			for polygon in polygons:
				simplify(polygon, options.simplification)


	def clip_polygons(self, polygons, viewbox):
		"""
		clip polygons to viewbox
		"""
		options = self.options
		if options.verbose: print "clipping"
		
		new_polygons = []
		
		for polygon in polygons:
			if polygon.id == '--': continue	
			# clip polygon, this may either remove or split the polygon
			clipped = gisutils.clip_to_rect(polygon, viewbox)			
			new_polygons += clipped

		return new_polygons


	def clip_polygons_to_sea(self, polygons, globe, view):
		options = self.options
		if options.verbose: print "clipping"
		
		sea_pts = self.get_sea_points(globe, view)
		
		new_polygons = []
		
		for polygon in polygons:
			if polygon.id == '--': continue	
			# clip polygon, this may either remove or split the polygon
			clipped = gisutils.clip_to_poly_pts(polygon, sea_pts)			
			new_polygons += clipped
		return new_polygons
	

	def group_polygons(self, polygons, groupBy):
		"""
		groups polygons that share a common attribute specified in groupBy parameter
		"""
		groups = []
		groupByAttr = {}
		nogroup = 0
		for poly in polygons:
			if groupBy in poly.data:
				attr = poly.data[groupBy]
			else:
				attr = 'na-%d'%nogroup
				nogroup += 1
			if attr in groupByAttr:
				grp = groupByAttr[attr]
			else:
				grp = groupByAttr[attr] = []
				groups.append(grp)
			grp.append(poly)
		return groups
	


	def add_map_layer(self, svg, polygons, layerId, filter=None, groupBy='oid', polycolor=None):
		"""
		add a layer to the map
		"""
		
		if filter != None:
			filtered = []
			for poly in polygons:
				if filter(poly):
					filtered.append(poly)
			polygons = filtered
			
		from svgfig import SVG
		from types import FunctionType
		
		svgGroup = SVG('g', id=layerId)
		svg.append(svgGroup)
		
		if groupBy != None:
			polyGroups = self.group_polygons(polygons, groupBy)
			for group in polyGroups:
				path_str_arr = []
				for poly in group:
					path_str_arr.append(poly.svgPathString(useInt=self.options.round_coordinates))
				
				# todo: looks ugly
				svg_path = SVG('path', d=' '.join(path_str_arr))
				poly = group[0]
				svg_path['data-iso'] = poly.id
				
				if type(polycolor) == FunctionType:
					svg_path['fill'] = polycolor(poly.data)
				
				for key in poly.data:
					svg_path['data-'+key] = poly.data[key]
						
				svgGroup.append(svg_path)
		else:
			for poly in polygons:			
				svg_path = SVG('path', d=poly.svgPathString(useInt=options.round_coordinates))
				if type(polycolor) == FunctionType:
					svg_path['fill'] = polycolor(poly.data)
				for key in poly.data:
					svg_path['data-'+key] = poly.data[key]
				svgGroup.append(svg_path)


	def get_sea_points(self, globe, view):
		sea = globe.sea_shape(self.options.llbbox)
		sea_pts = []
		for s in sea:
			x,y = view.project(s)	
			sea_pts.append(Point(x,y))
		return sea_pts
		

	def add_sea_layer(self, svg, globe, view, viewbox):
		from svgfig import SVG
		
		sea_pts = self.get_sea_points(globe, view)	
		sea_polys = self.clip_polygons([Polygon('sea', sea_pts, mode='point')], viewbox)	
		g = SVG('g', id='sea')
		svg.append(g)
		for sea in sea_polys:
			g.append(SVG('path', d=sea.svgPathString(useInt=False), style='fill:#d0ddf0', id="sea"))


	def add_graticule(self, svg, globe, view, viewbox):
		"""
		"""
		from clipping import Line
		from svgfig import SVG
		
		options = self.options
		lon0 = options.proj_opts['lon0']
		llbbox = options.llbbox
		
		minLat = max(globe.minLat, options.llbbox[1])
		maxLat = min(globe.maxLat, options.llbbox[3])
		minLon = options.llbbox[0]
		maxLon = options.llbbox[2]
		
		#print minLon, maxLon, minLat, maxLat
		
		def xfrange(start, stop, step):
			while (step > 0 and start < stop) or (step < 0 and start > step):
				yield start
				start += step

		g = SVG('g', id='graticule')
		svg.append(g)
		for lat in xfrange(0,90, options.grat_step):
			lats = ([lat, -lat], [0])[lat == 0]
			for lat_ in lats:
				if lat_ < minLat or lat_ > maxLat:
					continue
				
				pts = []
				lines = []
				for lon in xfrange(0,361,1):
					lon_ = lon-180
					if lon_ < minLon or lon_ > maxLon:
						continue
					
					if globe._visible(lon_, lat_):
						x,y = view.project(globe.project(lon_, lat_))
						pts.append(Point(x,y))
					else:
						if len(pts) > 1:
							line = Line(pts)
							pts = []
							lines += line & viewbox
				
				if len(pts) > 1:
					line = Line(pts)
					pts = []
					lines += line & viewbox
					
				for line in lines:
					path = SVG('path', d=line.svgPathString(), data_lat=lat_)
					if lat == 0:
						path['class'] = 'equator'
					g.append(path)
		
		for lon in xfrange(0,181, options.grat_step):
			lons = ([lon, -lon], [lon])[lon == 0 or lon == 180]
			for lon_ in lons:
				if lon_ < minLon or lon_ > maxLon:
					continue
				pts = []
				lines = []
				lat_range = xfrange(options.grat_step, 181-options.grat_step,1)
				if lon_ % 90 == 0:
					lat_range = xfrange(0, 181,1)
				for lat in lat_range:
					lat_ = lat-90
					if lat_ < minLat or lat_ > maxLat:
						continue
					if globe._visible(lon_, lat_):
						x,y = view.project(globe.project(lon_, lat_))
						pts.append(Point(x,y))
					else:
						if len(pts) > 1:
							line = Line(pts)
							pts = []
							lines += line & viewbox
				
				if len(pts) > 1:
					line = Line(pts)
					pts = []
					lines += line & viewbox
					
				for line in lines:
					path = SVG('path', d=line.svgPathString(), data_lon=lon0 - lon_)
					g.append(path)
					
				
				
	def add_locations(self, svg, globe, view, country_iso3, iso3, iso2, locations, radius=1.3, fills=None):
		"""
		for debugging purposes only, this functions draws geoip locations on the map
		"""
		if fills is None: fills = {}
		if country_iso3 == iso3:
			loc_csv = csv.reader(open('../data/maxmind/geolitecity/GeoLiteCity-Location.csv'))
			skip = 2
			for loc in loc_csv:
				if skip > 0: 
					skip -= 1
					continue
				if loc[1] == iso2 and loc[2] in locations:
					lat = float(loc[5])
					lon = float(loc[6])
					x,y = globe.project(lon, lat)
					pt = view.project(Point(x,y))
					if loc[2] in fills:
						color = fills[loc[2]]
					else:
						color = '#c00'
					svg.append(SVG('circle', cx=pt.x, cy=pt.y, r=str(radius), fill=color, stroke='none', opacity='.8'))
		
	
	def get_view(self, bbox):
		"""
		returns the output view
		"""
		options = self.options
		
		if not options.force_ratio:
			options.out_ratio = bbox.width / float(bbox.height)
				
		w = options.out_width
		h = options.out_height
		ratio = options.out_ratio
			
		if h == None:
			h = w / ratio
		elif w == None:
			w = h * ratio
	
		return View(bbox, w, h-1, padding=options.out_padding)
		
	
	def get_country_center(self, shp, iso3=None):
		"""
		either computes the center of a shape or uses customized center coordinates
		"""
		if iso3 != None and iso3 in custom_country_center:
			return custom_country_center[iso3]
		else:
			return gisutils.shape_center(shp)
	
		
	def render_world_map(self, outfile=None):
		"""
		renders a world map
		"""	
		options = self.options
		globe = options.projection(**options.proj_opts)
		llbbox = options.llbbox
		
		bbox = globe.world_bounds(llbbox)
	
		view = self.get_view(bbox)	
		viewbox = Bounds2D(width=view.width, height=view.height)
		
		svg = self.init_svg_canvas(view, bbox, globe)
	
		if options.sea_layer:
			self.add_sea_layer(svg, globe, view, viewbox)
		
		if options.graticule:
			self.add_graticule(svg, globe, view, viewbox)
		
		polygons = self.get_polygons_world(globe, view)
		
		self.simplify_polygons(polygons)
		
		if options.cut_lakes:
			polygons = self.cut_lakes(polygons, globe, view, viewbox)
		
		if options.llbbox != (-180,-90,180,90):
			polygons = self.clip_polygons_to_sea(polygons, globe, view)
		
		self.add_map_layer(svg, polygons, 'countries', groupBy='iso')
		self.save_or_display(svg, 'worldmap', outfile)
	
	
	
	def render_countries(self, target_iso3s, outfile=None):
		"""
		renders a single map that contains at least the specified countries
		in most cases, the map will also contain other countries
		"""
		# get shapes for the selected countries
		options = self.options
		targets = []
		for iso3 in target_iso3s:
			shprec = { 'shape': self.get_country_shape(iso3), 'record': self.get_country_record(iso3) }
			targets.append(shprec)
			
		proj_opts = options.proj_opts.copy()
		
		
			
		if not options.force_lat0 or not options.force_lon0:
			# get shape centers and use mean center as map center
			clons = []
			clats = []
			for i in range(len(targets)):
				tgt = targets[i]
				iso3 = target_iso3s[i]
				lon0, lat0 = self.get_country_center(tgt['shape'], iso3=iso3)
				clons.append(lon0)
				clats.append(lat0)
			
			if not options.force_lon0: proj_opts['lon0'] = min(clons) + (max(clons) - min(clons)) * .5
			if not options.force_lat0: proj_opts['lat0'] = min(clats) + (max(clats) - min(clats)) * .5
			if options.verbose:
				print 'computed map center at %f,%f' % (proj_opts['lon0'], proj_opts['lat0'])
					
		# initialize map projection
		globe = options.projection(**proj_opts)
		
		# project countries to get bounding boxes
		# and compute total bounding box and view
		bbox = Bounds2D()
		for i in range(len(targets)):
			iso3 = target_iso3s[i]
			shp = targets[i]['shape']
			cbox = self.get_country_bbox(iso3, globe)
			bbox.join(cbox)
				
		view = self.get_view(bbox)
		viewBox = Bounds2D(width=view.width, height=view.height)	
	
		# init svg
		svg = self.init_svg_canvas(view, bbox, globe)
		
		# add sea background
		if options.sea_layer:
			self.add_sea_layer(svg, globe, view, viewBox)
		
		if options.graticule:
			self.add_graticule(svg, globe, view, viewBox)
		
		
		# render every country that intersects the view
		polygons = self.get_polygons_countries(viewBox, view, globe)
		self.simplify_polygons(polygons)
		
		if options.cut_lakes:
			polygons = self.cut_lakes(polygons, globe, view, viewBox)
		
		polygons = self.clip_polygons(polygons, viewBox)
		
		_focus = lambda p: p.id in target_iso3s
		_context = lambda p: p.id not in target_iso3s
		
		self.add_map_layer(svg, polygons, 'context', groupBy='iso', filter=_context)
		self.add_map_layer(svg, polygons, 'countries', groupBy='iso', filter=_focus)
		
		# save and exit
		self.save_or_display(svg, '-'.join(target_iso3s), outfile)
	
	
	
	
	
	def render_regions_or_country(self):
		
		options = self.options
		import os, os.path
		
		load_shapefiles()
		
		iso_codes = options.target_countries
		
		if len(iso_codes) == 1 and iso_codes[0] == 'all':
			iso_codes = []
			for iso3, area in country_areas:
				if iso3 in ignore:
					print "ignoring", iso3
					continue
				iso_codes.append(iso3)
		
		out_path = '.'
		out_base = None
		
		if options.out_file != None:
			out_path = os.path.dirname(options.out_file)
			if len(iso_codes) == 1:
				out_base = os.path.basename(options.out_file)
			
		for iso3 in iso_codes:	
			if options.out_file != None:
				outfile = out_path + os.sep if out_path != "" else ""
				if out_base != None: outfile += out_base
				else: outfile += iso3+'.svg'
			else:
				outfile = None
				
			if outfile != None and options.target_countries[0] == 'all' and not options.force_overwrite:
				if os.path.isfile(outfile):
					# skip, map exists
					print "skipping %s - %s already exist"
					continue
		
			if options.add_context:
				render_country_and_context(iso3, regions=(command == "regions"), outfile=outfile)
			else:
				render_country(iso3, outfile=outfile, regions=(command == "regions"))
				
		
	def render_country(self, iso3, regions=False, outfile=None, focusRegion=None):
		"""
		renders a single country or its regions
		"""
		shp = self.get_country_shape(iso3)
		rec = self.get_country_record(iso3)
		
		options = self.options
		
		proj_opts = options.proj_opts.copy()
			
		if focusRegion == None:
			shp = self.get_country_shape(iso3) # get center shape
			center_lon, center_lat = self.get_country_center(shp, iso3=iso3)	
		else:
			shp2 = self.get_region_shape(iso3, focusRegion)
			center_lon, center_lat = gisutils.shape_center(shp2)	
		
		if not options.force_lat0: proj_opts['lat0'] = center_lat
		if not options.force_lon0: proj_opts['lon0'] = center_lon
		
		# initialize projection, use center lat/lng from shape record as center
		globe = options.projection(**proj_opts)
	
		if focusRegion == None:
			bbox = self.get_country_bbox(iso3, globe)	
		else:
			bbox = self.get_region_bbox(iso3, globe, focusRegion)
		
		view = self.get_view(bbox)
		viewbox = Bounds2D(width=view.width, height=view.height)	
	
		svg = self.init_svg_canvas(view, bbox, globe)
		
		# add sea background
		if options.sea_layer:
			self.add_sea_layer(svg, globe, view, viewbox)
	
		if options.graticule:
			self.add_graticule(svg, globe, view, viewbox)
			
		if options.verbose: print "rendering country "+iso3, regions
		
		polygons = self.get_polygons_country(iso3, view, globe, regions=regions)
		
		if regions and options.join_regions:
			polygons = self.join_regions(iso3, polygons)
		
		self.simplify_polygons(polygons)
		
		if options.cut_lakes:
			polygons = self.cut_lakes(polygons, globe, view, viewbox)
		
		polygons = self.clip_polygons(polygons, viewbox)
		
		self.add_map_layer(svg, polygons, iso3, groupBy=('iso','oid')[regions])
				
		self.save_or_display(svg, iso3, outfile)
	
	
	def render_country_and_context(self, iso3, regions=False, outfile=None, focusRegion=None):
		"""
		renders a country with surrounding countries
		"""
		options = self.options
		
		proj_opts = options.proj_opts.copy()
			
		if focusRegion == None:
			shp = self.get_country_shape(iso3) # get center shape
			center_lon, center_lat = self.get_country_center(shp, iso3=iso3)	
		else:
			shp = self.get_region_shape(iso3, focusRegion)
			center_lon, center_lat = gisutils.shape_center(shp)	
		
		if not options.force_lat0: proj_opts['lat0'] = center_lat
		if not options.force_lon0: proj_opts['lon0'] = center_lon
		
		# initialize projection, use center lat/lng from shape record as center
		globe = options.projection(**proj_opts)
	
		if focusRegion == None:
			bbox = self.get_country_bbox(iso3, globe)	
		else:
			bbox = self.get_region_bbox(iso3, globe, focusRegion)		
		
		# calculate view
		view = self.get_view(bbox)
		viewbox = Bounds2D(width=view.width, height=view.height)
	
		svg = self.init_svg_canvas(view, bbox, globe)
		
		# add sea background
		if options.sea_layer:
			self.add_sea_layer(svg, globe, view, viewbox)
	
		if options.graticule:
			self.add_graticule(svg, globe, view, viewbox)
		
		if options.verbose: print "rendering country with context", iso3
		
		polygons = self.get_polygons_country_context(iso3, viewbox, view, globe, regions=regions)
		
		if regions and options.join_regions:
			polygons = self.join_regions(iso3, polygons)
		
		_focus = lambda p: p.id == iso3
		_context = lambda p: p.id != iso3
		
		self.simplify_polygons(polygons, focusFilter=_focus)
		
		if options.cut_lakes:
			polygons = self.cut_lakes(polygons, globe, view, viewbox)
		
		polygons = self.clip_polygons(polygons, viewbox)
		
		self.add_map_layer(svg, polygons, 'context', groupBy='iso', filter=_context)
		self.add_map_layer(svg, polygons, iso3, groupBy=('iso','oid')[regions], filter=_focus)
	
		# add geoip locations for debbugging purpose
		
		# draw_locations(svg, globe, view, country_iso3, "FIN", "FI", ['01'], fills={'03':'#c00', '06':'#03c'})	
	
		self.save_or_display(svg, iso3, outfile)
	
	
	
	def add_shapefile_layer(self, svg_src, shp_src, data_column=None, outfile=None, polycolor=None):
		"""
		adds the content of a shapefile as a new map layer
		"""
		import svgfig, shapefile
		
		if data_column == None: data_column = ()
		
		options = self.options
		
		svg = svgfig.load(svg_src)
		
		svg_views = svg[1][0]
		
		svg_view = svg_views[0]
		svg_proj = svg_view[0]
		svg_bbox = svg_view[1]
		
		pd = float(svg_view['padding'])
		
		globe = proj.Proj.fromXML(svg_proj)
		bbox = Bounds2D(left=float(svg_bbox['x']), top=float(svg_bbox['y']), width=float(svg_bbox['w']), height=float(svg_bbox['h']))
		
		vh = float(svg_view['h'])
		vw = float(svg_view['w'])
		
		options.out_width = vw
		options.out_height = vh
		options.force_ratio = True
		options.out_padding = pd
		
		view = self.get_view(bbox)
		viewbox = Bounds2D(width=view.width, height=view.height)

		if options.verbose:			
			print view
			print viewbox
			print globe
			
		# eventually crop at layer
		layer_poly = None
		if options.crop_at_layer != None:
			from Polygon import Polygon as Poly
			from Polygon.IO import writeSVG
			from gisutils import restore_poly_from_path_str
			
			if options.verbose:
				print 'crop at layer "%s"' %  options.crop_at_layer
			for g in svg[2:]:
				if g['id'] == options.crop_at_layer:
					if options.verbose:
						print 'found layer!'
					# restore polygons from that layer
					layer_poly = Poly()
					for path in g[:]:
						path_str = path['d']
						poly = restore_poly_from_path_str(path_str)
						layer_poly = layer_poly | poly
					break
			
		# read shapefile
		
		sf = shapefile.Reader(shp_src)
		
		fields = []
		for f in sf.fields[1:]:
			fields.append(f[0].lower().replace('_','-'))
		
		shprecs = sf.shapeRecords()
		polygons = []
		
		for sx in range(len(shprecs)):
			shp = shprecs[sx].shape
			rec = shprecs[sx].record
			data = {  }
			for i in data_column:
				data[fields[i]] = Utils.remove_unicode(rec[i])
			
			polys = self.get_shape_polygons(shp, "", globe, view, data=data)
			for poly in polys:
				if poly.bbox.intersects(viewbox):
					polygons.append(poly)
		
		polygons = self.merge_biggest_polygons(polygons, 400)
		
		self.simplify_polygons(polygons)
		
		if options.cut_lakes:
			polygons = self.cut_lakes(polygons, globe, view, viewbox)
		
		polygons = self.clip_polygons(polygons, viewbox)
		
		if layer_poly != None:
			from gisutils import polygon_to_poly, poly_to_polygons
			out = []
			for polygon in polygons:
				poly = polygon_to_poly(polygon)
				poly_ = poly & layer_poly
				if poly_ != None:
					out += poly_to_polygons(poly_, id=polygon.id, data=polygon.data, closed=polygon.closed)
			polygons = out
			
		
			
		self.add_map_layer(svg, polygons, options.layer_id, polycolor=polycolor)
		
		self.save_or_display(svg, "", outfile)
		

	def save_or_display(self, svg, iso3, outfile):
		"""
		this finally saves the SVG map or displays it in firefox 
		"""
		options = self.options
		import os, os.path
		
		if outfile != None or (options.target_countries != None and options.target_countries[0] == 'all'):
			if outfile == None: outfile = 'tmp/'+iso3+'.svg'
			if not os.path.isdir('tmp'):
				os.mkdir('tmp')
			# svg.save(outfile)
			open(outfile, 'w').write(svg.standalone_xml(indent="  ", newl=""))
			if options.verbose: print "stored as "+outfile
		else:
			svg.firefox()


	def get_lake_polygons(self, globe, view, viewbox):
		"""
		"""
		recs = self.sf_recs['lakes']
		lake_polys = []
		for i in range(len(recs)):
			rec = recs[i]
			if rec[1] < 1:
				shp = self.get_shape('lakes', i)
				lakes = self.get_shape_polygons(shp, 'lakes', globe, view)
				for lake in lakes:
					if lake.bbox.intersects(viewbox): # check if polygon intersects view
						lake_polys.append(lake)
		return lake_polys
	
	
	def cut_lakes(self, polygons, globe, view, viewbox):
		"""
		cuts lake polygons out of country polygons
		"""
		from gisutils import poly_to_polygons, polygon_to_poly
		
		if self.options.verbose:
			print "cutting out lakes"
		
		lakes = self.get_lake_polygons(globe, view, viewbox)
		
		self.simplify_polygons(lakes)
		
		lake_polys = []
		for lake in lakes:
			lake_poly = polygon_to_poly(lake)
			if lake_poly is not None:
				lake_polys.append(lake_poly)
		
		out = []
		for polygon in polygons:
			poly = polygon_to_poly(polygon)
			if poly is None:
				continue
			for lake in lake_polys:
				poly = poly - lake
			out += poly_to_polygons(poly, id=polygon.id, data=polygon.data, closed=polygon.closed)
		return out
		
		
	def merge_biggest_polygons(self, polygons, area_thresh=1000):
		out = []
		join = []
		
		for poly in polygons:
			area = poly.area()
			if area < area_thresh:
				out.append(poly)
			else:
				join.append(poly)
				
		out += gisutils.merge_polygons(join)
			
		return out



class SVGMapOptions(object):
	"""
	this class stores all options = self.options needed by this script
	"""
	def __init__(self):
		self.out_width = None
		self.out_height = None
		self.out_ratio = None
		self.out_padding_perc = 0.0 # percentage padding of min(width,height) 
		self.outfile = None
		self.force_ratio = False
		self.data_path = 'data/'
		self.add_context = False
		self.shp_country_id_col = 2
		self.force_overwrite = False
		self.simplification = 2
		self.round_coordinates = False
		self.context_simplification = None
		self.verbose = False
		self.target_countries = None
		self.sea_layer = False
		
		self.projection = None
		self.force_proj = False
		
		# options for add layer mode
		self.shapefile_src = None
		self.svg_src = None
		self.layer_id = None
		self.crop_at_layer = None
		self.layer_data_column = ()
	
		# options for regions mode
		self.join_regions = False
		
		# options for world mode
		
		# graticule options
		self.graticule = False
		self.grat_step = 15
		
		# options for the projection, will be passed to projection via **
		self.proj_opts = { 'lat0': 0, 'lon0': 0 }
		self.force_lat0 = False
		self.force_lon0 = False
		
		self.cut_lakes = False
	
	
	def applyDefaults(self, command=""):
	
		dw = 500    # defaults
		dr = 1.67
		dp = 0
	
		ow = self.out_width
		oh = self.out_height
		ratio = self.out_ratio
	
		if ow == None and oh == None:
			ow = 900
			
		if ow != None and oh != None:
			self.force_ratio = True
			ratio = ow / float(oh)
		
		if self.context_simplification == None:
			self.context_simplification = self.simplification
			
		if ow != None and oh != None:
			self.out_padding = min(ow, oh) * self.out_padding_perc
		elif ow != None:
			self.out_padding = ow * self.out_padding_perc
		else:
			self.out_padding = oh * self.out_padding_perc
		
		self.ratio = ratio
		self.out_width = ow
		self.out_height = oh
		
		if self.out_padding is None:
			self.out_padding = dp

		if self.projection is None:
			if command in ("country","regions","countries","region"):
				self.projection = proj.LAEA		
				print "LAEA"
			else:
				self.projection = proj.NaturalEarth
		
		if self.layer_id == None:
			self.layer_id = 'layer'
			
		if self.llbbox == None:
			self.llbbox = (-180,-90,180,90)



class Utils:
	@staticmethod
	def remove_unicode(str):
		"""
		taken from http://stackoverflow.com/questions/1207457/convert-unicode-to-string-in-python-containing-extra-symbols
		"""
		import unicodedata
		if isinstance(str, unicode):
			return unicodedata.normalize('NFKD', str).encode('ascii','ignore')	
		else:
			return str

if __name__ == '__main__':
	# some tests
	options = SVGMapOptions()
	options.verbose = False
	options.applyDefaults()
	
	import sys
	
	def _test(str, res):
		print '\n   ::%s::\n   ' % str,
		print res
		return res
	
	
	svgmap = SVGMap(options)
	from proj import Robinson, LAEA, Stereographic
	

	svgmap.add_shapefile_layer('DE.svg', '../misc/de-wahlkreise/wahlkreise', data_columns=(2,4))

	exit()
	
	proj = Robinson()

	
	_test('get shape', svgmap.get_shape('countries', 123))
	DEU = _test('shape index', svgmap.country_index['DEU'])
	rec = svgmap.get_country_record('DEU')
	_test('get_country_record', rec[:5]+['...'])
	shp = _test('get_country_shape', svgmap.get_country_shape('DEU'))
	_test('shape area', '%.2f sqkm'%svgmap.shape_area('countries', DEU))
	_test('country region indices', svgmap.get_country_region_indices('DEU')[:5]+['...'])
	bbox = _test('country bbox', svgmap.get_country_bbox('DEU', proj))
	view = _test('init view', View(bbox, 400,300,10))
	_test('init svg', svgmap.init_svg_canvas(view, bbox, proj)[:])
	_test('get shp polys', svgmap.get_shape_polygons(shp,'DEU',proj,view)[:2]+['...'])
	_test('get poly data', svgmap.get_polygon_data(rec))
	#	_test('get_country_shape', svgmap.get_country_shape('DEU'))

	svgmap.options.projection = LAEA

	_test('render country', svgmap.render_country('DEU'))
	_test('render regions', svgmap.render_country('DEU', regions=True))
	#_test('render regions w context', svgmap.render_country_and_context('DEU', regions=True))
	
	svgmap.options.sea_layer = True
	svgmap.options.graticule = 15
	svgmap.options.projection = Robinson
	svgmap.options.lon0 = -100
	svgmap.options.force_lon0 = True
	
	#_test('render world map', svgmap.render_world_map())
	
	svgmap.options.projection = Stereographic
	svgmap.options.lat0 = 90
	svgmap.options.force_lat0 = True
	
	#_test('render world map (2)', svgmap.render_world_map())

	svgmap.options.force_lat0 = False
	svgmap.options.force_lon0 = False
	svgmap.options.out_padding = 30
	
	_test('render countries', svgmap.render_countries(['ESP','FRA','DEU','GBR','ITA']))
	
	
	print