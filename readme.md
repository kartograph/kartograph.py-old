svgmap
======

**svgmap** is a simple toolset that helps to create interactive thematic maps that run across multiple browsers without using tile-based mapping environments like Google Maps or OpenStreetMaps. Think of it as OpenLayers, but *a lot* more simple to use.

## How it works

Basically, a Python script generates SVG files that are loaded and rendered by a JS class.

### The Python side

**svgmap.py** is a small Python script that renders SVG maps out of shapefiles. At the moment it can be used from the command line.

For instance, if you want an SVG map of Brazil you type:

	svgmap.py country BRA --o Brazil.svg

Of course, there are plenty of possible options, see readme in svgmap.py directory.

### The JavaScript side

**svgmap.js** will then load the SVG maps and allows to connect the maps with some data. You can color the map polygons (which could be countries, for instance) to get a chloropleth map, or you can add labels or charts at geo-locations etc.

Again, see readme in svgmap.js directory to get more information.
