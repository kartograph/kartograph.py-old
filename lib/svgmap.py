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

	
ignore = set('ATA')


# exceptions for some countries
country_min_area = {}
country_min_area['JPN'] = .1
country_min_area['AUS'] = .01
country_min_area['CAN'] = .05
country_min_area['ALA'] = .1
country_min_area['FRA'] = .2
country_min_area['DNK'] = .1
country_min_area['ITA'] = .1
country_min_area['GBR'] = .165
country_min_area['ESP'] = .165


custom_country_center = {}
custom_country_center['USA'] = (-98.606,39.622)


import shapefile, csv, sys

from svgfig import *
from lib.gisutils import *
from lib import proj

def load_shapefiles():
	"""
	0: prepare hires shapefiles
	""" 
	global command, options
	global country_sf, country_recs, country_shapes, country_index, country_areas, join_csv_src 
	
	country_sf_src = options.data_path + 'shp/ne_10m_admin_0_countries'
	region_sf_src = options.data_path + 'shp/ne_10m_admin_1_states_provinces_shp'
	join_csv_src = options.data_path + 'region_joins.csv'

	if options.verbose: print "loading country shapefile"
	
	country_sf = shapefile.Reader(country_sf_src)
	country_recs = country_sf.records()
	
	if command not in ('world','countries') and not options.add_context:
		country_shapes = None
	else:
		country_shapes = country_sf.shapeRecords()
	
	country_areas = []
	
	country_index = {}
	
	for i in range(len(country_recs)):
		iso3 = country_recs[i][29]
		country_index[iso3] = i
		if country_shapes: 
			country_areas.append([iso3, shape_area(country_shapes[i].shape)])
	
	country_areas = sorted(country_areas, key=lambda row: row[1]*-1)
	
	if command == 'regions':
		global region_sf, region_recs
		region_sf = shapefile.Reader(region_sf_src)
		region_recs = region_sf.records()
		
	

def get_country_shape(iso3):
	"""
	1: get the shape record of the target country
	"""
	global country_recs, country_shapes, country_index
	
	country_shape = None
	
	i = country_index[iso3]
	
	country_record = country_recs[i]
	if country_shapes:
		country_shape = country_shapes[i]
	else:
		country_shape = country_sf.shapeRecord(i)
	
	if country_shape == None:
		print "no shape found for country %s" % iso3
		return None
		
	return country_shape


def get_country_region_shapes(country_iso3):
	"""
	returns a list of region shapes for a country
	"""
	country_region_shapes = []
	for i in range(len(region_recs)):
		iso3 = region_recs[i][2]
		if iso3 == country_iso3:
			country_region_shapes.append(i)
	return country_region_shapes
	
	
	
def get_bounding_box(iso3, shape, globe):
	""" 
	3: render most important shapes to get clipping rect
	"""	
	min_area_percent = 0.2

	if iso3 in country_min_area:
		min_area_percent = country_min_area[iso3]

	parts = shape.parts[:]
	parts.append(len(shape.points))
	max_area = 0
	areas = []
	for j in range(0,len(parts)-1):
		pts = shape.points[parts[j]:parts[j+1]]
		a = area(pts)
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


def init_svg_canvas(view, bbox, globe, center_lat, center_lon):
	"""
	prepare a blank new svg file
	"""
	from svgfig import canvas, SVG
	
	w = view.width
	h = view.height+2
	
	svg = canvas(width='%dpx' % w, height='%dpx' % h, viewBox='0 0 %d %d' % (w, h), enable_background='new 0 0 %d %d' % (w, h), style='stroke-width:0.7pt; stroke-linejoin: round; stroke:#444; fill:white;')

	css = 'path { fill-rule: evenodd; }\n#context path { fill: #eee; stroke: #bbb; } '
	
	if options.graticule:
		css += '#graticule path { fill: none; stroke-width:0.25pt;  } #graticule .equator { stroke-width: 0.5pt } '

	svg.append(SVG('defs', SVG('style', css, type='text/css')))

	meta = SVG('metadata')
	
	views = SVG('views')
	
	view = SVG('view', padding=str(options.out_padding))
	
	proj = globe.toXML()
	bbox = SVG('bbox', x=round(bbox.left,2), y=round(bbox.top,2), w=round(bbox.width,2), h=round(bbox.height,2))
	
	views.append(view)
	view.append(proj)
	proj.append(bbox)
	
	meta.append(views)
	svg.append(meta)
	
	return svg


"""
helper functions for get_country_polygons()
"""
def _addPolygons(polygons, polys):
	for poly in polys:
		polygons.append(poly)


def _testPolygon(polygon, viewBox):
	return polygon.bbox.intersects(viewBox)



def _getPolygons(shp, id, globe, view, data=None):
	"""
	projects a shapefile shape and returns a list of polygons
	"""
	parts = shp.parts[:]
	parts.append(len(shp.points))
	polys = []
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
			polygon = Polygon(id, poly_points, mode='point', data=data)
			if polygon != None:
				polys.append(polygon)
	return polys

def _remove_unicode(str):
	"""
	taken from http://stackoverflow.com/questions/1207457/convert-unicode-to-string-in-python-containing-extra-symbols
	"""
	import unicodedata
	return unicodedata.normalize('NFKD', str).encode('ascii','ignore')	

def _get_polygon_data(rec, regions=False):
	if regions:
		data = { 'oid': rec[0], 'iso': rec[2] }
		if rec[7] != "":
			data['hasc'] = rec[7]
		if rec[19] != "":
			data['fips'] = rec[19][-2:]
		if rec[7] == "" and rec[19] == "":
			data['name'] =  _remove_unicode(rec[4].decode('ISO 8859-1'))
	else:
		data = { 'iso': rec[29] }
	return data	

def get_polygons_country(iso3, shprec, viewBox, view, globe, regions=False):
	"""
	---
	"""
	global options
	
	if regions:
		country_region_shapes = get_country_region_shapes(iso3)
		polys = []
		for j in country_region_shapes:
			rec = region_recs[j]
			shp = region_sf.shapeRecord(j).shape
			_addPolygons(polys, _getPolygons(shp, iso3, globe, view, data=_get_polygon_data(rec, regions=True)))
	else:
		shp = shprec.shape
		rec = shprec.record
		polys = _getPolygons(shp, iso3, globe, view, data=_get_polygon_data(rec))
		
	return polys
	

def get_polygons_country_context(country_iso3, shprec, viewBox, view, globe, regions=False):
	"""
	returns a list of gisutils.Polygon that will be visible in the map
	"""
	polygons = []
	
	global options, country_recs, country_shapes, region_recs, region_sf
	
	focus_shape = shprec.shape
	focus_rec = shprec.record
	
	if regions:
		country_region_shapes = get_country_region_shapes(country_iso3)
	
	for i in range(len(country_recs)):
		iso3 = country_recs[i][29].upper()
		if iso3 != country_iso3:
			# this is not the center country	
			shp = country_shapes[i].shape
			polys = _getPolygons(shp, iso3, globe, view, data=_get_polygon_data(country_recs[i]))
			
			for poly in polys:
				if poly.bbox.intersects(viewBox):
					polygons.append(poly)			
		
		else:
			# this is the center country
			if regions and len(country_region_shapes) > 0:
				# we have regions for this country
				for j in country_region_shapes:
					rec = region_recs[j]
					shp = region_sf.shapeRecord(j).shape
					_addPolygons(polygons, _getPolygons(shp, iso3, globe, view, data=_get_polygon_data(rec, regions=True)))
			else:
				# we don't have regions, instead use the country itself
				_addPolygons(polygons, _getPolygons(focus_shape, iso3, globe, view))
				
				if regions and options.verbose:
					print "..no regions for ",iso3
	return polygons


def get_polygons_countries(viewBox, view, globe, regions=False):
	"""
	returns a list of gisutils.Polygon that will be visible in the map
	"""
	polygons = []
	
	for i in range(len(country_recs)):
		iso3 = country_recs[i][29].upper()
		shp = country_shapes[i].shape
		polys = _getPolygons(shp, iso3, globe, view, data=_get_polygon_data(country_recs[i]))
		
		for poly in polys:
			if poly.bbox.intersects(viewBox):
				polygons.append(poly)			
		
	return polygons



def join_regions(iso3, polygons):
	"""
	at some exceptional cases, country regions need to be merged
	"""
	import csv
	
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
		
	



def simplify_polygons(polygons, focusFilter=None):
	"""
	simplifies or generalizes a list of polygons
	"""
	global options
	
	if options.verbose: print "simplifying polygons"
	# join duplicate points
	unify(polygons)
	
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


def clip_polygons(polygons, viewBox):
	"""
	clip polygons to viewbox
	"""
	global options
	if options.verbose: print "clipping and rendering"
	
	new_polygons = []
	
	for polygon in polygons:
		if polygon.id == '--': continue
	
		# clip polygon, this may either remove or split the polygon
		clipped = clipToRect(polygon, viewBox)	
			
		for poly in clipped:
			new_polygons.append(poly)
		
	return new_polygons



def group_polygons(polygons, groupBy):
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
	


def add_map_layer(svg, polygons, layerId, filter=None, groupBy='oid'):
	"""
	add a layer to the map
	"""
	if filter != None:
		filtered = []
		for poly in polygons:
			if filter(poly):
				filtered.append(poly)
		polygons = filtered
		
	svgGroup = SVG('g', id=layerId)
	svg.append(svgGroup)
	
	print layerId, groupBy
	
	if groupBy != None:
		polyGroups = group_polygons(polygons, groupBy)
		for group in polyGroups:
			path_str_arr = []
			for poly in group:
				path_str_arr.append(poly.svgPathString(useInt=options.round_coordinates))
			
			# todo: looks ugly
			svg_path = SVG('path', d=' '.join(path_str_arr))
			poly = group[0]
			svg_path['data-iso'] = poly.id
			
			for key in poly.data:
				svg_path['data-'+key] = poly.data[key]
					
			svgGroup.append(svg_path)
	else:
		for poly in polygons:			
			svg_path = SVG('path', d=poly.svgPathString(useInt=options.round_coordinates))
			for key in poly.data:
				svg_path['data-'+key] = poly.data[key]
			svgGroup.append(svg_path)
	

def add_sea_layer(svg, globe, view, viewbox):
	sea = globe.sea_shape()
	sea_pts = []
	for s in sea:
		x,y = view.project(s)	
		sea_pts.append(Point(x,y))
		
	sea_polys = clip_polygons([Polygon('sea', sea_pts, mode='point')], viewbox)	
	g = SVG('g', id='sea')
	svg.append(g)
	for sea in sea_polys:
		g.append(SVG('path', d=sea.svgPathString(useInt=False), style='fill:#d0ddf0', id="sea"))


def add_graticule(svg, globe, view, viewbox):
	"""
	"""
	from lib.clipping import Line
	g = SVG('g', id='graticule')
	svg.append(g)
	for lat in range(0,90, options.grat_step):
		lats = ([lat, -lat], [0])[lat == 0]
		for lat_ in lats:
			pts = []
			lines = []
			for lon in range(0,361,1):
				lon_ = lon-180
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
	
	for lon in range(0,181, options.grat_step):
		lons = ([lon, -lon], [lon])[lon == 0 or lon == 180]
		for lon_ in lons:
			pts = []
			lines = []
			for lat in range(0,181,1):
				lat_ = lat-90
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
				path = SVG('path', d=line.svgPathString(), data_lon=options.lon0 - lon_)
				g.append(path)
				
				
				
def draw_locations(svg, globe, view, country_iso3, iso3, iso2, locations, radius=1.3, fills=None):
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
	
	
def get_view(bbox):
	"""
	returns the output view
	"""
	global options
	
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
	

def get_country_center(shp, iso3=None):
	"""
	either computes the center of a shape or uses customized center coordinates
	"""
	global custom_country_center
	
	if iso3 != None and iso3 in custom_country_center:
		return custom_country_center[iso3]
	else:
		return shape_center(shp)



def get_polygons_world(globe, view):
	"""
	returns a list of gisutils.Polygon that will be visible in the map
	"""
	polygons = []
		
	for i in range(len(country_recs)):
		shp = country_shapes[i].shape
		iso3 = country_recs[i][29]
		polys = _getPolygons(shp, iso3, globe, view, data=_get_polygon_data(country_recs[i]))
			
		for poly in polys:
			polygons.append(poly)			
	
	return polygons



""" -----------------
WORLD MAP CODE BELOW
------------------"""

def render_world_map():
	"""
	...
	"""	
	globe = options.projection(lon0=options.lon0, lat0=options.lat0)
	
	#bbox = Bounds2D()
	bbox = globe.world_bounds()
	
	view = get_view(bbox)	
	viewbox = Bounds2D(width=view.width, height=view.height)
	
	lat0, lon0 = (0.0, 0.0)
	svg = init_svg_canvas(view, bbox, globe, lat0, lon0)

	if options.sea_layer:
		add_sea_layer(svg, globe, view, viewbox)
	
	if options.graticule:
		add_graticule(svg, globe, view, viewbox)
	
	load_shapefiles()	
	polygons = get_polygons_world(globe, view)
	simplify_polygons(polygons)
	add_map_layer(svg, polygons, 'countries', groupBy='iso')
	save_or_display(svg, 'worldmap', options.out_file)





def render_regions_or_country():
	
	global options
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
			
	
def render_country(iso3, outfile=None, regions=False):
	"""
	renders a single country
	"""
	shprec = get_country_shape(iso3)
	rec = shprec.record
	shp = shprec.shape
	
	center_lon, center_lat = get_country_center(shp, iso3=iso3)	
	if options.force_lat0: center_lat = options.lat0
	if options.force_lon0: center_lon = options.lon0
	globe = options.projection(lon0=center_lon, lat0=center_lat)	
	bbox = get_bounding_box(iso3, shp, globe)
	
	view = get_view(bbox)
	viewbox = Bounds2D(width=view.width, height=view.height)	

	svg = init_svg_canvas(view, bbox, globe, center_lat, center_lon)
	
	# add sea background
	if options.sea_layer:
		add_sea_layer(svg, globe, view, viewbox)

	if options.graticule:
		add_graticule(svg, globe, view, viewbox)
		
	if options.verbose: print "rendering country "+iso3, regions
	
	polygons = get_polygons_country(iso3, shprec, viewbox, view, globe, regions=regions)
	
	if regions and options.join_regions:
		polygons = join_regions(iso3, polygons)
	
	simplify_polygons(polygons)
	
	#polygons = clip_polygons(polygons, viewbox)
	add_map_layer(svg, polygons, iso3, groupBy=('iso','oid')[regions])
			
	save_or_display(svg, iso3, outfile)





# get projection center, either from options or from geometry
# initialize projection
# get bbox for view
# init view
# init canvas
# eventually add sea and graticula
# get polygons to be displayed in view


def render_country_and_context(iso3, outfile=None, regions=False):
	"""
	renders a country with surrounding countries
	"""
	global options
	
	shprec = get_country_shape(iso3) # get center shape
	shp = shprec.shape

	# initialize projection, use center lat/lng from shape record as center
	center_lon, center_lat = get_country_center(shp, iso3=iso3)	
	if options.force_lat0: center_lat = options.lat0
	if options.force_lon0: center_lon = options.lon0
	globe = options.projection(lon0=center_lon, lat0=center_lat)

	bbox = get_bounding_box(iso3, shp, globe)
	
	# calculate view
	view = get_view(bbox)
	viewbox = Bounds2D(width=view.width, height=view.height)

	svg = init_svg_canvas(view, bbox, globe, center_lat, center_lon)
	
	# add sea background
	if options.sea_layer:
		add_sea_layer(svg, globe, view, viewbox)

	if options.graticule:
		add_graticule(svg, globe, view, viewbox)
	
	if options.verbose: print "rendering country with context", iso3
	
	polygons = get_polygons_country_context(iso3, shprec, viewbox, view, globe, regions=regions)
	
	if regions and options.join_regions:
		polygons = join_regions(iso3, polygons)
	
	_focus = lambda p: p.id == iso3
	_context = lambda p: p.id != iso3
	
	simplify_polygons(polygons, focusFilter=_focus)
	
	polygons = clip_polygons(polygons, viewbox)
	
	add_map_layer(svg, polygons, 'context', groupBy='iso', filter=_context)
	add_map_layer(svg, polygons, iso3, groupBy=('iso','oid')[regions], filter=_focus)

	# add geoip locations for debbugging purpose
	
	# draw_locations(svg, globe, view, country_iso3, "FIN", "FI", ['01'], fills={'03':'#c00', '06':'#03c'})	

	save_or_display(svg, iso3, outfile)



def add_shapefile_layer():
	"""
	adds the content of a shapefile as a new map layer
	"""
	import svgfig
	
	svg = svgfig.load(options.svg_src)
	
	b = map(float, svg[1][0][2][0].split(','))
	bbox = Bounds2D(left=b[0], top=b[1], width=b[2], height=b[3])
	pj = svg[1][0][0][0]
	pd = float(svg[1][0][3][0])
	clon,clat = map(float, svg[1][0][1][0].split(','))
	vh = float(svg['height'][:-2])
	vw = float(svg['width'][:-2])
	
	options.out_width = vw
	options.out_height = vh
	options.force_ratio = True
	options.out_padding = pd
	
	view = get_view(bbox)
	viewbox = Bounds2D(width=view.width, height=view.height)
	
	if pj == "laea":
		globe = proj.LAEA(clat, clon)
	elif pj == "naturalearth":
		globe = proj.NaturalEarth()
	elif pj == "satellite":
		globe = proj.Satellite(clat,clon)
		
		
	# eventually crop at layer
	layer_poly = None
	if options.crop_at_layer != None:
		from Polygon import Polygon as Poly
		from Polygon.IO import writeSVG
		from gisutils import restore_poly_from_path_str
		
		print 'crop at layer "%s"' %  options.crop_at_layer
		for g in svg[2:]:
			if g['id'] == options.crop_at_layer:
				print 'found layer!'
				# restore polygons from that layer
				layer_poly = Poly()
				for path in g[:]:
					path_str = path['d']
					poly = restore_poly_from_path_str(path_str)
					layer_poly = layer_poly | poly
				break
		
	# read shapefile
	
	sf = shapefile.Reader(options.shapefile_src)
	
	fields = []
	for f in sf.fields:
		fields.append(f[0].lower().replace('_','-'))
	
	shprecs = sf.shapeRecords()
	polygons = []
	
	for sx in range(len(shprecs)):
		shp = shprecs[sx].shape
		rec = shprecs[sx].record
		data = { 'sx': sx }
		for i in range(len(rec)):
			data[fields[i]] = rec[i]
		polys = _getPolygons(shp, "", globe, view, data=data)
		for poly in polys:
			if poly.bbox.intersects(viewbox):
				polygons.append(poly)
	
	
	simplify_polygons(polygons)
	
	polygons = clip_polygons(polygons, viewbox)
	
	if layer_poly != None:
		from gisutils import polygon_to_poly, poly_to_polygons
		out = []
		for polygon in polygons:
			poly = polygon_to_poly(polygon)
			poly_ = poly & layer_poly
			if poly_ != None:
				out += poly_to_polygons(poly_, id=polygon.id, data=polygon.data)
		polygons = out
		
	add_map_layer(svg, polygons, 'layer')
	
	save_or_display(svg, "", options.out_file)
	

def render_countries(outfile=None):
	"""
	renders a single map that contains at least the specified countries
	in most cases, the map will also contain other countries
	"""
	# get shapes for the selected countries
	load_shapefiles()
	targets = []
	for iso3 in options.target_countries:
		shprec = get_country_shape(iso3)
		targets.append(shprec)
		
	if not options.force_lat0 or not options.force_lon0:
		# get shape centers and use mean center as map center
		clons = []
		clats = []
		for i in range(len(targets)):
			tgt = targets[i]
			iso3 = options.target_countries[i]
			lon0, lat0 = get_country_center(tgt.shape, iso3=iso3)
			clons.append(lon0)
			clats.append(lat0)
		
		if not options.force_lon0: options.lon0 = min(clons) + (max(clons) - min(clons)) * .5
		if not options.force_lat0: options.lat0 = min(clats) + (max(clats) - min(clats)) * .5
		if options.verbose:
			print 'computed map center at %f,%f' % (options.lon0, options.lat0)
				
	# initialize map projection
	globe = options.projection(lon0=options.lon0, lat0=options.lat0)
	
	if isinstance(globe, proj.Conic):
		globe = options.projection(lon0=options.lon0, lat0=options.lat0, lat1=options.lat1, lat2=options.lat2)
	
	# project countries to get bounding boxes
	# and compute total bounding box and view
	bbox = Bounds2D()
	for i in range(len(targets)):
		iso3 = options.target_countries[i]
		shp = targets[i].shape
		cbox = get_bounding_box(iso3, shp, globe)
		bbox.join(cbox)
			
	view = get_view(bbox)
	viewBox = Bounds2D(width=view.width, height=view.height)	

	# init svg
	svg = init_svg_canvas(view, bbox, globe, options.lat0, options.lon0)
	
	# add sea background
	if options.sea_layer:
		add_sea_layer(svg, globe, view, viewBox)
	
	if options.graticule:
		add_graticule(svg, globe, view, viewBox)
	
	
	# render every country that intersects the view
	polygons = get_polygons_countries(viewBox, view, globe)
	simplify_polygons(polygons)
	polygons = clip_polygons(polygons, viewBox)
	add_map_layer(svg, polygons, 'countries', groupBy='iso')
	
	# save and exit
	save_or_display(svg, '-'.join(options.target_countries), outfile)







def save_or_display(svg, iso3, outfile):
	"""
	this finally saves the SVG map or displays it in firefox 
	"""
	global options
	
	if outfile != None or (options.target_countries != None and options.target_countries[0] == 'all'):
		if outfile == None: outfile = 'tmp/'+iso3+'.svg'
		if not os.path.isdir('tmp'):
			os.mkdir('tmp')
		# svg.save(outfile)
		open(outfile, 'w').write(svg.standalone_xml(indent="  ", newl=""))
		if options.verbose: print "stored as "+outfile
	else:
		svg.firefox()





class Options(object):
	"""
	this class stores all global options needed by this script
	"""
	def __init__(self):
		self.out_width = None
		self.out_height = None
		self.out_ratio = None
		self.out_padding_perc = 0.0 # percentage padding of min(width,height) 
		self.out_file = None
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
		
		# options for add layer mode
		self.shapefile_src = None
		self.svg_src = None
		self.layer_id = None
		self.crop_at_layer = None
	
		# options for regions mode
		self.join_regions = False
		
		# options for world mode
		self.lat0 = 0.0
		self.lon0 = 0.0
		self.lat1 = 0.0
		self.lat2 = 0.0
		self.force_lat0 = False
		self.force_lon0 = False
		self.force_lat1 = False
		self.force_lat2 = False
	
		# graticule options
		self.graticule = False
		self.grat_step = 15
		
	
	def applyDefaults(self):
	
		dw = 500    # defaults
		dr = 1.67
		dp = 0
	
		ow = self.out_width
		oh = self.out_height
		ratio = self.out_ratio
	
		if ow == None and oh == None:
			ow = 500
			
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
			if command == "world":
				self.projection = proj.NaturalEarth
			else:
				self.projection = proj.LAEA

