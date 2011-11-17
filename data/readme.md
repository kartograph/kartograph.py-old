In order to get svgmap.py to work, you need to download some Natural Earth shapefiles.

	mkdir shp
	cd shp
	wget http://www.nacis.org/naturalearth/10m/cultural/10m-admin-0-countries.zip
	unzip 10m-admin-0-countries.zip
	rm 10m-admin-0-countries.zip
	wget http://www.nacis.org/naturalearth/10m/cultural/10m-admin-1-states-provinces-shp.zip
	unzip 10m-admin-1-states-provinces-shp.zip
	rm 10m-admin-1-states-provinces-shp.zip

At the end, the content of this directory should look like this:

	custom-region-joins.csv
	readme.md
	region_joins.csv
	./shp:
		ne_10m_admin_0_countries.dbf
		ne_10m_admin_0_countries.prj
		ne_10m_admin_0_countries.shp
		ne_10m_admin_0_countries.shx
		ne_10m_admin_1_states_provinces_shp.dbf
		ne_10m_admin_1_states_provinces_shp.prj
		ne_10m_admin_1_states_provinces_shp.shp
		ne_10m_admin_1_states_provinces_shp.shx