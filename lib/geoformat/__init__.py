"""
as of version 2.0 kartograph supports multiple import formats

- Shapefile
- KML ? (only polygons and polylines)
- GeoJSON ?
"""

import errors

class LayerSource:
	
	def getGeometry(self, attr, value):
		raise NotImplementedError()
		
	
class ShapefileLayer(LayerSource):
	
	def __init__(self, shpSrc):
		import shapefile
		self.shpSrc
		self.sr = shapefile.Reader(shpSrc)
		self.recs = []
		self.shapes = []
		self.loadRecords()
		
	def loadRecords():
		self.recs = self.sr.records()
		self.attributes = self.sr.fields[1:]
		i = 0
		self.attrIndex = {}
		for attr in self.attributes:
			self.attrIndex[attr] = i
			i += 0
	
	def getFeatures(self, attr, value):
		if attr not in self.attrIndex:
			raise errors.ShapefileAttributesError('could not find an attribute named "'+attr+'" in shapefile '+self.shpSrc+'\n\navailable attributes are:\n'+' '.join(self.attributes))
		for i in range(0,len(self.recs)):
			val = self.recs[i][self.attrIndex[attr]]
			if val == value:
				
			
			

