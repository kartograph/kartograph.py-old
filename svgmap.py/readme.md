svgmap.py
=====

**svgmap.py** is a Python script that renders shapefiles to SVG maps. At the moment, the country shapesfiles are taken from the Natural Earth project.

### Prerequisites

The following Python libraries are required:

* [shapefile](http://packages.python.org/Python%20Shapefile%20Library/)
* [Polygon](http://pypi.python.org/pypi/Polygon/1.17)
* [svgfig](http://code.google.com/p/svgfig/)

### Global Options

The following global options are avaiable

* **--width**, **-w** output width
* **--height**, **-h** output height
* **--ratio**, **-r** output ratio (will be used to compute missing width or height)
* **--quality**, **-q** quality level 0..100, see Quality section below
* **--output**, **-o** filename for the SVG map, if not provided *tmp.svg* will be used.
* **--padding**, **-p** how much spacing should be added around the map content
* **--force-overwrite**, **-f** by default, existing files will not be overwritten in batch mode, unless you set this parameter


## Available Commands

Currently the the following *commands* are available

	svgmap.py world
	svgmap.py country
	svgmap.py regions
	svgmap.py layer

### World Map

The command **svgmap.py world** renders a map of all countries in the world. Currently, the [Natural Earth Projection](http://www.shadedrelief.com/NE_proj/)  is used, but more projections will be added in the future. 

For instance, this will output a world map the file world.svg:

	svgmap.py world --sea --width 600 --o world.svg

![world map](https://github.com/gka/svgmap/raw/master/svgmap.py/doc/world.svg.png)

Command-specific options are:

* **--sea**, **-s** adds a sea background to the map

### Country Map

Renders maps that are centered on a country.

Usage:

	svgmap.py country ISOCODES

To render a map of Germany to DE.svg, simply type

	svgmap.py country DEU --height 300 -o DEU.svg

![Map of Germany](https://github.com/gka/svgmap/raw/master/svgmap.py/doc/DEU.svg.png)

In the next example, the surrounding countries are added using the *--context* parameter. Also, a padding of 3% is set.

	svgmap.py country DEU --h 300 --context --sea --padding 10 --ratio 2 -o DEU-context.svg

![Region map of Germany](https://github.com/gka/svgmap/raw/master/svgmap.py/doc/DEU-context.svg.png)

You can render several country maps at once by providing a comma-separated list of ISO-codes. In this case, only the directory name of the *--output* parameter will be used and the country maps are saved under their iso3 codes. 

	svgmap.py country DEU,FRA

Also, you can render country maps for *all* countries, although this may take a while to finish.

	svgmap.py country all

Command-specify options are:

* **--context**, **-c** includes "surrounding" countries in the map to provide some context
* **--context-quality** use this if you want to set a different quality for the context (usually a lower quality)
* **--sea** will add a background indicating the sea

### Region Map

Basically just like the **country** command, but for the selected country, the administrative-level-1 regions will be rendered instead of the country. Provides the same options as country.

	svgmap.py regions FRA --h 300 -o FRA-regions.svg

![Region map of France](https://github.com/gka/svgmap/raw/master/svgmap.py/doc/FRA-regions.svg)

	svgmap.py regions FRA --h 300 --context --sea --padding 10 --ratio 2 -o FRA-regions-context.svg

![Region map of France with context](https://github.com/gka/svgmap/raw/master/svgmap.py/doc/FRA-regions-context.svg)


### Adding Shapefile Layers

This can be used to add another layer to a SVG map. 

## Details 

### Quality

The quality level will be used to compute the parameter for the polygon simplification (also called *generalization*). A quality of 100 means no simplification.

