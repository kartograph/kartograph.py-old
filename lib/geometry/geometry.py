

		
class Geometry:

	def project(self, proj):
		"""
		project geometry
		"""
		raise NotImplementedError('project() is not implemented')
	
	
class SolidGeometry(Geometry):

	def area():
		raise NotImplementedError('area() is not implemented')
		
	def invalidate(self):
		self.__area = None