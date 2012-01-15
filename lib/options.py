
"""
API 2.0
helper methods for validating options dictionary
"""

import os.path, proj


class OptionParseError(Exception):
    """Base class for exceptions in this module."""
    pass    
Error = OptionParseError

def is_str(s):
	return isinstance(s, (str, unicode))

def parse_options(opts):
	"""
	check out that the option dict is filled correctly
	"""
	# projection
	parse_proj(opts)
	parse_layers(opts)
	#parse_bounds(opts)
	#parse_export(opts)


def parse_proj(opts):
	"""
	checks projections
	"""
	if 'proj' not in opts: opts['proj'] = {}
	prj = opts['proj']
	if 'id' not in prj: prj['id'] = 'laea'
	if prj['id'] not in proj.projections:
		raise Error('unknown projection')
	prjClass = proj.projections[prj['id']]
	for attr in prjClass.attributes():
		if attr not in prj:
			prj[attr] = "auto"
	

def parse_layers(opts):
	if 'layers' not in opts: opts['layers'] = []
	l_id = 0
	for layer in opts['layers']:
		if 'src' not in layer:
			raise Error('you need to define the source for your layers')
		if not os.path.exists(layer['src']):
			raise Error('layer source not found: '+layer['src'])
		if 'id' not in layer:
			layer['id'] = 'layer_'+str(l_id)
			l_id += 1
		parse_layer_attributes(layer)
		parse_layer_filter(layer)
		parse_layer_join(layer)
		parse_layer_simplify(layer)	

			
def parse_layer_attributes(layer):
	if 'attributes' not in layer:
		layer['attributes'] = []
		return
	attrs = []
	for attr in layer['attributes']:
		if is_str(attr):
			attrs.append({'src':attr, 'tgt': attr })
		else:
			attrs.append(attr)


def parse_layer_filter(layer):
	if 'filter' not in layer:
		layer['filter'] = False
		return
	filter = layer['filter']
	if 'type' not in filter: filter['type'] = 'include'
	if 'attribute' not in filter: 
		raise Error('layer filter must define an attribute to filter on')
	if 'equals' in filter:
		if is_str(filter['equals']): 
			filter['equals'] = [filter['equals']]
	elif 'greater-than' in filter:
		try:
			filter['greater-than'] = float(filter['greater-than'])
		except ValueError:
			raise Error('could not convert filter value "greater-than" to float')
	elif 'less-than' in filter:
		try:
			filter['less-than'] = float(filter['less-than'])
		except ValueError:
			raise Error('could not convert filter value "less-than" to float')
	else:
		raise Error('you must define either "equals", "greater-than" or "less-than" in the filter')

	
def parse_layer_join(layer):
	if 'join' not in layer:
		layer['join'] = False
		return
		
		
def parse_layer_simplify(layer):
	if 'simplify' not in layer:
		layer['simplify'] = False
		return
	try:
		layer['simplify'] = float(layer['simplify'])
	except ValueError:
		raise Error('could not convert simplification amount to float')