#!/usr/bin/env python2.7
"""
This python script renders a map of a given country along with its neighbor countries

new Natural Earth version
"""

import sys, os.path, getopt

def usage():
	print '\nUsage: '+os.path.basename(sys.argv[0])+' command'
	print 'Possible commands are:\n'
	
	print '   country      renders country boundary'
	print '   regions      renders all admin-level 1 regions of a country'
	print '   region       renders a single admin-level 1 region of a country'
	print '   world        renders world map'
	print '   layer        adds a new layer from a shapefile'
	print
	
	
def main():
	global command, options
	
	parse_args()
	
	if command == "world":
		render_world_map()
	elif command in ("country", "regions"):
		render_regions_or_country()
	elif command == "region":
		render_region()
	elif command == "layer":
		add_shapefile_layer()

def parse_args():
	global command, options, math
	
	options = Options()
	
	if len(sys.argv) < 2:
		usage()
		sys.exit(2)
	
	command = sys.argv[1]
	
	if command not in ('country','regions','world','layer','region'):
		usage()
		sys.exit(2)
	
	# parse options
	# global options
	opt_str = "o:w:h:r:p:q:sfv"
	long_opt = ['output=', 'width=', 'height=', 'ratio=', 'padding=', 'quality=', 'sea', 'force-overwrite', 'context-quality=', 'verbose']

	if command == "world":
		long_opt += ['graticule']
		cmd_args = sys.argv[2:]
	
	if command in ('regions', 'country'):
		if len(sys.argv) < 3:
			print '\nError: you must define the country to be rendered, e.g.\n\n   '+os.path.basename(sys.argv[0])+' '+command+' USA'
			print '   '+os.path.basename(sys.argv[0])+' '+command+' USA,CAN,MEX\n   '+os.path.basename(sys.argv[0])+' '+command+' all'
			print
			sys.exit(2)
		else:
			options.target_countries = sys.argv[2].split(',')
			long_opt += ['context']
			opt_str += "c"	
			cmd_args = sys.argv[3:]
	
	if command == "layer":
		if len(sys.argv) < 4:
			print "\nError: you must provide a svg-map and a shapefile\n\n"+os.path.basename(sys.argv[0])+' '+command+' SVGMAP.svg SHAPEFILE'
		else:
			long_opt += ['layer-id=', 'crop-at-layer=']
			options.svg_src = sys.argv[2]
			options.shapefile_src = sys.argv[3]
			cmd_args = sys.argv[4:]
	
	try:
		opts, args = getopt.getopt(cmd_args, opt_str, long_opt)
		
		for o, a in opts:
			if o in ('-w', '--width'):
				options.out_width = int(a)
			elif o in ('-h', '--height'):
				options.out_height = int(a)
			elif o in ('-r', '--ratio'):
				options.out_ratio = float(a)
				options.force_ratio = True
			elif o in ('-v', '--verbose'):
				options.verbose = True
			elif o in ('-o', '--output'):
				options.out_file = a
			elif o in ('-c', '--context'):
				options.add_context = True
			elif o in ('-p', '--padding'):
				options.out_padding_perc = float(a)/100
			elif o in ('-q', '--quality'):
				q = max(0, min(100, float(a)))/100.0
				options.simplification = 100 - math.pow(q,.25)*100
			elif o in ('--context-quality'):
				q = max(0, min(100, float(a)))/100.0
				options.context_simplification = 100 - math.pow(q,.25)*100
			elif o in ('-s', '--sea'):
				options.sea_layer = True
			elif o in ('-f', '--force-overwrite'):
				options.force_overwrite = True
			elif o == '--crop-at-layer':
				options.crop_at_layer = a
			elif o == '--layer-id':
				options.layer_id = a

		options.applyDefaults()
		
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)
	


	
ignore = set('ATA')


# exceptions for some countries
country_min_area = {}
country_min_area['JPN'] = .1
country_min_area['AUS'] = .01
country_min_area['CAN'] = .05
country_min_area['ALA'] = .1
country_min_area['DNK'] = .1
country_min_area['ITA'] = .1
country_min_area['GBR'] = .01


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

	print "loading country shapefile"
	
	country_sf = shapefile.Reader(country_sf_src)
	country_recs = country_sf.records()
	
	if command != "world" and not options.add_context:
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
	
	for j in range(0,len(parts)-1):
		pts = shape.points[parts[j]:parts[j+1]]
		if areas[j] >= max_area * min_area_percent:
			latlon = []
			for k in range(0,len(pts)):
				latlon.append((pts[k][1], pts[k][0]))
					
			points = globe.plot(latlon)
			for xy in points:
				pt = Point(xy[0], xy[1])
				bbox.update(pt)
	return bbox


def init_svg_canvas(view, bbox, globe, center_lat, center_lon):
	"""
	prepare a blank new svg file
	"""
	from svgfig import canvas, SVG
	
	global options
	
	w = view.width
	h = view.height+2
	
	svg = canvas(width='%dpx' % w, height='%dpx' % h, viewBox='0 0 %d %d' % (w, h), enable_background='new 0 0 %d %d' % (w, h), style='stroke-width:1px; stroke-linejoin: round; stroke:#444; fill:white;')

	svg.append(SVG('defs', SVG('style', 'path { fill-rule: evenodd; }\n#context path { fill: #eee; stroke: #bbb; }', type='text/css')))

	meta = SVG('metadata')
	
	proj = SVG('view', SVG('proj', globe.name), SVG('center', '%f,%f' % (center_lat,center_lon)), SVG('bbox', '%.2f,%.2f,%.2f,%.2f' % (round(bbox.left,2), round(bbox.top,2), round(bbox.width,2), round(bbox.height,2))), SVG('padding', str(options.out_padding)))
	
	meta.append(proj)
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
	for j in range(0,len(parts)-1):
		pts = shp.points[parts[j]:parts[j+1]]
		latlon = []
		for k in range(0,len(pts)):
			latlon.append((pts[k][1], pts[k][0]))
		poly_points = []
		points = globe.plot(latlon)
		if points == None: continue
		for xy in points:
			poly_points.append(view.project(Point(xy[0], xy[1])))
		polygon = Polygon(id, poly_points, mode='point', data=data)
		if polygon != None:
			polys.append(polygon)
	return polys


def _get_polygon_data(rec, region=False):
	if region:
		data = { 'region':rec[7], 'oid': rec[0], 'iso': rec[2] }
	else:
		data = { 'iso': rec[29] }
	if sx != None:
		data['sx'] = sx
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
				_addPolygons(polygons, _getPolygons(focus_shape, iso3, globe, view, country_index[iso3]))
				if regions and options.verbose:
					print "..no regions for ",iso3
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
		if 'objectid' in poly.data and str(poly.data['objectid']) in join_map:
			regId = join_map[str(poly.data['objectid'])]
			if regId == '': regId = 'n/a'
			if regId not in groups:
				groups[regId] = []
			groups[regId].append(poly)
		else:
			out.append(poly)
	
	for gid in groups:
		polys = merge_polygons(groups[gid], id=iso3, data={ 'subid': gid })
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
	for poly in polygons:
		if groupBy in poly.data:
			attr = poly.data[groupBy]
		else:
			attr = 'na'
		if attr in groupByAttr:
			grp = groupByAttr[attr]
		else:
			grp = groupByAttr[attr] = []
			groups.append(grp)
		grp.append(poly)
	return groups
	


def add_map_layer(svg, polygons, layerId, filter=None, useInt=True, groupBy='objectid'):
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
	
	polyGroups = group_polygons(polygons, groupBy)
	
	for group in polyGroups:
		path_str_arr = []
		for poly in group:
			path_str_arr.append(poly.svgPathString(useInt=useInt))
		
		svg_path = SVG('path', d=' '.join(path_str_arr))
		poly = group[0]
		# svg_path['data-iso'] = poly.id
		
		for key in poly.data:
			svg_path['data-'+key] = poly.data[key]
				
		svgGroup.append(svg_path)
	

def draw__map(country_iso3, svg, polygons, useInt=True, randomColors=False, labels=False):
	"""
	DEPRECATED, use add_map_layer instead
	add country polygons to SVG
	"""
	from svgfig import SVG
	from gisutils import polygon_center
	
	polyGroups = group_polygons(polygons)
	
	for group in polyGroups:
		path_str_arr = []
		for poly in group:
			path_str_arr.append(poly.svgPathString(useInt=useInt))
		
		svg_path = SVG('path', d=' '.join(path_str_arr))
		poly = group[0]
		
		if poly.id != country_iso3:
			svg_polygon['class'] = 'n'
		
		svg_polygon['id'] = poly.id
		
		if 'subid' in poly.data and poly.data['subid'] != "":
			svg_polygon['subid'] = poly.data['subid']
		if 'objectid' in poly.data and poly.data['objectid'] != "":
			svg_polygon['oid'] = poly.data['objectid']
		
		svg.append(svg_polygon)
		
		known_ids = []
		if randomColors:
			import random
			rand_colors = []
		
		if labels:
			center = polygon_center(poly)
			l = poly.id
			if 'subid' in poly.data: 
				l=poly.data['subid'][3:]
			if randomColors:
				if l not in known_ids:
					known_ids.append(l)
					color = 'HSL('+str(random.randrange(0,360))+',90%,90%)'
					rand_colors.append(color)
				else:
					color = rand_colors[known_ids.index(l)]
				svg_polygon['fill'] = color
			text = SVG('text', l, x=center.x, y=center.y, text_anchor='middle', alignment_baseline='central', style="stroke:none;font-size:9px;fill:black;font-family;Lato;font-weight:400;")
			svg.append(text)	


	
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
				x,y = globe.project(lat, lon)
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
	

def get_country_center(iso3, shp):
	"""
	either computes the center of a shape or uses customized center coordinates
	"""
	global custom_country_center
	
	if iso3 in custom_country_center:
		return custom_country_center[iso3]
	else:
		return shape_center(shp)


""" -----------------
WORLD MAP CODE BELOW
------------------"""

def render_world_map():
	"""
	...
	"""	
	globe = proj.NaturalEarth()
	
	bbox = Bounds2D()
	
	for lat,lon in [(0,-180),(0,180),(-90,0),(90,0)]:
		x,y = globe.project(lat,lon)
		bbox.update(Point(x,y))
		
	view = get_view(bbox)	
	
	lat0, lon0 = (0.0, 0.0)
	svg = init_svg_canvas(view, bbox, globe, lat0, lon0)

	if options.sea_layer:
		sea = []
		for lat in range(-90,90): sea.append((-180,lat))
		for lon in range(-180,180): sea.append((lon, 90))
		for lat in range(-90,90): sea.append((180,lat*-1))
		for lon in range(-180,180): sea.append((lon*-1, -90))
		
		sea_pts = []
		
		for s in sea:
			lon, lat = s
			x,y = globe.project(lat, lon)
			pt = view.project(Point(x,y))	
			sea_pts.append(pt)
			
		sea = Polygon('sea', sea_pts, mode='point')	
		svg.append(SVG('path', d=sea.svgPathString(useInt=False), style='fill:#d0ddf0', id="sea"))
	
	load_shapefiles()	
	polygons = get_polygons_world(globe, view)
	simplify_polygons(polygons)
	add_map_layer(svg, polygons, 'countries')
	save_or_display(svg, 'worldmap', options.out_file)




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
	
	center_lon, center_lat = get_country_center(iso3, shp)
	globe = proj.LAEA( center_lat , center_lon )
	
	bbox = get_bounding_box(iso3, shp, globe)
	
	view = get_view(bbox)
	viewBox = Bounds2D(width=view.width, height=view.height)	

	svg = init_svg_canvas(view, bbox, globe, center_lat, center_lon)
	
	# add sea background
	if options.sea_layer:		
		svg.append(SVG('g', SVG('rect', x=0, y=0, width=view.width, height=view.height, style='stroke:none;fill:#d0ddf0'), id="bg"))
		
	if options.verbose: print "rendering country "+iso3, regions
	
	polygons = get_polygons_country(iso3, shprec, viewBox, view, globe, regions=regions)
	
	simplify_polygons(polygons)
	
	polygons = clip_polygons(polygons, viewBox)
	
	add_map_layer(svg, polygons, iso3, groupBy='iso')
			
	save_or_display(svg, iso3, outfile)



def render_country_and_context(iso3, outfile=None, regions=False):
	"""
	renders a country with surrounding countries
	"""
	global options
	
	shprec = get_country_shape(iso3) # get center shape
	shp = shprec.shape

	# initialize projection, use center lat/lng from shape record as center
	center_lon, center_lat = get_country_center(iso3, shp)
	
	globe = proj.LAEA( center_lat , center_lon )

	bbox = get_bounding_box(iso3, shp, globe)
	
	# calculate view
	view = get_view(bbox)
	viewBox = Bounds2D(width=view.width, height=view.height)

	svg = init_svg_canvas(view, bbox, globe, center_lat, center_lon)
	
	# add sea background
	if options.sea_layer:
		svg.append(SVG('g', SVG('rect', x=0, y=0, width=view.width, height=view.height, style='stroke:none;fill:#d0ddf0'), id="bg"))
	
	if options.verbose: print "rendering country with context", iso3
	
	polygons = get_polygons_country_context(iso3, shprec, viewBox, view, globe, regions=regions)
	
	polygons = join_regions(iso3, polygons)
	
	_focus = lambda p: p.id == iso3
	_context = lambda p: p.id != iso3
	
	simplify_polygons(polygons, focusFilter=_focus)
	
	polygons = clip_polygons(polygons, viewBox)
	
	#draw_map(country_iso3, svg, polygons)
	add_map_layer(svg, polygons, 'context', filter=_context, groupBy='objectid')
	add_map_layer(svg, polygons, iso3, filter=_focus, groupBy='iso')

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
	pj = svg[1][0][0][0]
	pd = float(svg[1][0][3][0])
	clat, clon = map(float, svg[1][0][1][0].split(','))
	bbox = Bounds2D(left=b[0], top=b[1], width=b[2], height=b[3])
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
	
	print len(polygons)
	
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
		
	add_map_layer(svg, polygons, 'layer', groupBy='sx')
	
	save_or_display(svg, "", options.out_file)
	

def save_or_display(svg, iso3, outfile):
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
		self.context_simplification = None
		self.verbose = False
		self.target_countries = None
		self.sea_layer = False
		
		# options for add layer mode
		self.shapefile_src = None
		self.svg_src = None
		self.layer_id = None
		self.crop_at_layer = None
	
	
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


if __name__ == "__main__":
    main()