svgmap.py
=====

**svgmap.py** is a Python script that renders shapefiles to SVG maps. The idea is to include any information that can be used to identify the represented geography. For instance, the path that represents Argentina will store the ISO-code in a data-attribute:

	<path data-iso="ARG" .. />

Also, the SVG files store information on the projection parameters, which can be used by the JS API to reconstruct the projection in order to add more geo-located layers and features (like markers).

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


### Available Commands

Currently the the following *commands* are available

	svgmap.py world
	svgmap.py country
	svgmap.py regions
	svgmap.py layer

## World Maps

The command **svgmap.py world** renders a map of all countries in the world. The shapefiles come from the [Natural Earth project](http://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/). Currently, the [Natural Earth Projection](http://www.shadedrelief.com/NE_proj/)  is used, but more projections will be added in the future. 

For instance, this will output a world map into world.svg:

	svgmap.py world --sea --width 600 --o world.svg

![world map](https://github.com/gka/svgmap/raw/master/svgmap.py/doc/world.svg.png)

Command-specific options are:

* **--sea**, **-s** adds a sea background to the map

## Country Maps

Renders maps that are centered on a country. You need to pass a three-letter country code ([ISO 3166-1 alpha 3](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-3)) as argument.

Usage:

	svgmap.py country ISO

To render a map of Germany you would run

	svgmap.py country DEU --height 300 -o DEU.svg

![Map of Germany](https://github.com/gka/svgmap/raw/master/svgmap.py/doc/DEU.svg.png)

In the next example, the surrounding countries are added using the *--context* parameter. Also, the padding is set to 10%  and the output ratio is set to 2 (width is two times height):

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

## Region Maps

Basically just like the **country** command, but for the selected country, the administrative-level-1 regions will be rendered instead of the country. Provides the same options as country.

	svgmap.py regions FRA --h 300 -o FRA-regions.svg

![Region map of France](https://github.com/gka/svgmap/raw/master/svgmap.py/doc/FRA-regions.svg.png)

You can add context the same way as in country maps.

	svgmap.py regions FRA --h 300 --context --sea --padding 10 --ratio 2 -o FRA-regions-context.svg

![Region map of France with context](https://github.com/gka/svgmap/raw/master/svgmap.py/doc/FRA-regions-context.svg.png)


## Adding Shapefile Layers

This can be used to add another layer to a SVG map. In general, every layer is represented by a SVG group (<g>). The following example demonstrates the feature:

At first we create a country map of Brazil with some context.

	svgmap country BRA --context --height 300 -p6 -s -o BRA.svg

![Map of Brazil with context](https://github.com/gka/svgmap/raw/master/svgmap.py/doc/BRA.svg.png)

Now we add a new layer for current forests, taken from [Global Forest Watch](http://ims.missouri.edu/gfwmetadataexplorer/).

	svgmap layer BRA.svg globalforestwatch/w_curr.shp -o BRA-forests.svg

![Map of Brazil with context](https://github.com/gka/svgmap/raw/master/svgmap.py/doc/BRA-forests.svg.png)

If we want just the forests in Brazil, we can use the *--crop-to-layer* parameter. We have to define the layer id to which the shapefile should be cropped to (in this case, the layer id is "BRA"):

	svgmap layer BRA.svg globalforestwatch/w_curr.shp --crop-to-layer=BRA -o BRA-forests-cropped.svg

![Map of Brazil with context](https://github.com/gka/svgmap/raw/master/svgmap.py/doc/BRA-forests-cropped.svg.png)

Command-specific parameters are:

* **--layer-id** will be used as id for the layer
* **--crop-to-layer** can be used to crop the shape to any existing layer


## Details 

### Quality

The quality level will be used to compute the parameter for the polygon simplification (also called *generalization*). The higher the quality, the less the polygons are simplified. A quality of 100 means no simplification. Note that the overall quality also depends on the output size.

![different qualities](https://github.com/gka/svgmap/raw/master/svgmap.py/doc/quality.png)

