from poly import PolyPolygon

Polygon = PolyPolygon


if __name__ == "__main__":	
	p = Polygon([[(0,0),(30,0),(15,30)]])
	print 'p', p.area()
	q = Polygon([[(10,5),(30,0),(15,20)]])
	print 'q', q.area()
	print 'p+q', (p+q).area()
	print 'p-q', (p-q).area()
	print 'p&q', (p&q).area()	
	print 'p|q', (p|q).area()



