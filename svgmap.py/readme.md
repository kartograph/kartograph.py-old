svgmap.py
=====

**svgmap.py** is a Python script that renders shapefiles to SVG maps. At the moment, the country shapesfiles are taken from the Natural Earth project.

### Prerequisites

The following Python libraries are required:

* shapefile
* Polygon
* SVGfig

### Commands and Global Options

Currently the the following *commands* are available

	svgmap.py world
	svgmap.py country
	svgmap.py regions
	svgmap.py layer

The following global options are avaiable

* **--width**, **-w** output width
* **--height**, **-h** output height
* **--ratio**, **-r** output ratio (will be used to compute missing width or height)
* **--quality**, **-q** quality level 0..100, see Quality section below
* **--output**, **-o** filename for the SVG map, if not provided *tmp.svg* will be used.
* **--padding**, **-p** how much spacing should be added around the map content

### Rendering a World Map

The command **svgmap.py world** renders a map of all countries in the world. For instance, this will output the file world.svg:

	svgmap.py world --sea --width 600 --o world.svg

The resulting SVG will look like this:

![world map]()

### Country Map

Renders maps that are centered on a country.

Usage:

	svgmap.py country ISOCODES

To render a map of Germany to DE.svg, simply type

	svgmap.py country DEU

You can render several country maps at once by providing a comma-separated list of ISO-codes. In this case, only the directory name of the *--output* parameter will be used and the country maps are saved under their iso3 codes. E.g:

	svgmap.py country DEU,FRA

#### Command Options

* **--context**, **-c** includes "surrounding" countries in the map to provide some context
* **--context-quality** use this if you want to set a different quality for the context (usually a lower quality)

### Region Map

Basically just like the **country** command, but for the selected country, the administrative-level-1 regions will be rendered instead of the country. Provides the same options as country.

### Adding Shapefile Layers

This can be used to add another layer to a SVG map. 

### Quality

The quality level will be used to compute the parameter for the polygon simplification (also called *generalization*). A quality of 100 means no simplification.

