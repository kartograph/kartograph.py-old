svgmap.py
=====

**svgmap.py** is a Python script that renders shapefiles to SVG maps. The main idea is to get geo-referenced vector maps. For instance, s path that represents Argentina will store the ISO-code in a data-attribute:

	<path data-iso="ARG" .. />

Also, the SVG files store information on the projection parameters, which can be used by the JS API to reconstruct the projection in order to add more geo-located layers and features (like markers).

**Note** that creating perfectly styled static maps is *not* the purpose of this script, so you won't find any options to set colors or styles. Instead, you will get really nice geo-references vector maps. They are intended to be rendered inside browsers where you can add lot's of CSS and JavaScript magic. Of course, you can open and edit them in Inkscape/Illustrator, too.

### Current Status

svgmap.py is quite stable and renders really nice maps. Though, a few more things need to be done in the future:

* packaging as real Python module + pydocs
* region maps
* multiple views per map (for instance to include Alaska and Hawaii to US map)
* and, of course, more map projections. Also see my [wishlist](http://www.progonos.com/furuti/MapProj/Dither/ProjTbl/projTbl.html).

### Prerequisites

The following Python libraries are required:

* [shapefile](http://packages.python.org/Python%20Shapefile%20Library/)
* [Polygon](http://pypi.python.org/pypi/Polygon/1.17)
* [svgfig](http://code.google.com/p/svgfig/)

Also you need to download Natural Earth shapefiles following these [download instructions](https://github.com/svgmap/svgmap.py/tree/master/data)

### Global Options

The following global options are avaiable

* **--width**, **-w** output width
* **--height**, **-h** output height
* **--ratio**, **-r** output ratio (will be used to compute missing width or height)
* **--quality**, **-q** quality level 0..100, see Quality section below
* **--output**, **-o** filename for the SVG map, if not provided *tmp.svg* will be used.
* **--padding**, **-p** how much spacing should be added around the map content
* **--force-overwrite**, **-f** by default, existing files will not be overwritten in batch mode, unless you set this parameter
* **--list-projections** prints a list of all available map projections


### Available Commands

Currently the the following *commands* are available

- world
- country
- regions
- layer
- countries


## Rendering world maps

The command **world** renders a map of all countries in the world. The shapefiles come from the [Natural Earth project](http://www.naturalearthdata.com/downloads/10m-cultural-vectors/10m-admin-0-countries/). 

For instance, this will output a world map into world.svg:

	svgmap.py world --sea --width 600 --o world.svg

[![world map](https://github.com/svgmap/svgmap.py/raw/master/doc/world.svg.png)](https://github.com/svgmap/svgmap.py/raw/master/doc/world.svg)

Also, you can now change the map projection and the center longitude:

	svgmap.py world --sea --proj=robinson --lon0=-78

![robinson map, centered on America](https://github.com/svgmap/svgmap.py/raw/master/doc/robinson-america.png)]

Command-specific options are:

* **--sea**, **-s** adds a sea background to the map
* **--proj** specify the map projection that should be used
* **--lon0** sets the center longitude

## Rendering country maps

The **country** command renders maps that are centered on a country. You need to pass a three-letter country code ([ISO 3166-1 alpha 3](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-3)) as argument. For the country and regions maps the [Lambert Azimuthal Equal-Area projection](http://en.wikipedia.org/wiki/Lambert_azimuthal_equal-area_projection) is used (again, more projections to come in future versions).

Usage:

	svgmap.py country ISO

To render a map of Germany you would run

	svgmap.py country DEU --height 300 -o DEU.svg

![Map of Germany](https://github.com/svgmap/svgmap.py/raw/master/doc/DEU.svg.png)

In the next example, the surrounding countries are added using the *--context* parameter. Also, the padding is set to 10%  and the output ratio is set to 2 (width is two times height):

	svgmap.py country DEU --h 300 --context --sea --padding 10 --ratio 2 -o DEU-context.svg

![Region map of Germany](https://github.com/svgmap/svgmap.py/raw/master/doc/DEU-context.svg.png)

You can render several country maps at once by providing a comma-separated list of ISO-codes. In this case, only the directory name of the *--output* parameter will be used and the country maps are saved under their iso3 codes. 

	svgmap.py country DEU,FRA

Also, you can render country maps for *all* countries, although this may take a while to finish.

	svgmap.py country all

Command-specify options are:

* **--context**, **-c** includes "surrounding" countries in the map to provide some context
* **--context-quality** use this if you want to set a different quality for the context (usually a lower quality)
* **--sea** will add a background indicating the sea

## Mapping all regions of a country

The **regions** (plural!) command works basically just like the *country* command, except for the selected country, the administrative-level-1 regions will be rendered instead of the country. The command provides the same parameters that are provided in the *country* command.

	svgmap.py regions FRA --h 300 -o FRA-regions.svg

![Region map of France](https://github.com/svgmap/svgmap.py/raw/master/doc/FRA-regions.svg.png)

For instance, you can add context the same way as in country maps.

	svgmap.py regions FRA --h 300 --context --sea --padding 10 --ratio 2 -o FRA-regions-context.svg

![Region map of France with context](https://github.com/svgmap/svgmap.py/raw/master/doc/FRA-regions-context.svg.png)

Command specific parameters:

* **--join-regions** join regions according to external region list (see below)

## Mapping a single region of a country

*NOT IMPLEMENTED, YET*

The **region** (singular!) command allows to render just a single region of a country.

	svgmap.py region FRA --fips A4

Command specific parameters:

* **--fips** define the focus region by FIPS code
* **--hasc** define the focus region by HASC code
* **--name** define the focus region by name (will try to match minor spelling differences)
* **--context** adds surrounding regions *and* countries
* **--region-context** adds surrounding regions (no countries here)

## Mapping multiple countries in one map

The **countries** command renders a map that contains multiple countries and it's surrounding context. The following renders a map that (at least) contains Spain, Portugal, France, Germany and the United Kingdom, and the Lambert Conformal Conical projection (lcc) will be used.

	svgmap.py countries ESP,PRT,FRA,DEU,GBR -p5 --proj=lcc -s

![some european countries](https://github.com/svgmap/svgmap.py/raw/master/doc/some-eu-countries.png)

## Adding Shapefile Layers

This can be used to add another layer to a SVG map. In general, every layer is represented by a SVG group (<g>). The following example demonstrates the feature:

At first we create a country map of Brazil with some context.

	svgmap.py country BRA --context --height 300 -p6 -s -o BRA.svg

![Map of Brazil with context](https://github.com/svgmap/svgmap.py/raw/master/doc/BRA.svg.png)

Now we add a new layer for current forests, taken from [Global Forest Watch](http://ims.missouri.edu/gfwmetadataexplorer/).

	svgmap.py layer BRA.svg globalforestwatch/w_curr.shp -o BRA-forests.svg

![Map of Brazil with context](https://github.com/svgmap/svgmap.py/raw/master/doc/BRA-forests.svg.png)

If we want just the forests in Brazil, we can use the *--crop-to-layer* parameter. We have to define the layer id to which the shapefile should be cropped to (in this case, the layer id is "BRA"):

	svgmap.py layer BRA.svg globalforestwatch/w_curr.shp --crop-to-layer=BRA -o BRA-forests-cropped.svg

![Map of Brazil with context](https://github.com/svgmap/svgmap.py/raw/master/doc/BRA-forests-cropped.svg.png)

Here's another example: After rendering a country map of the United States we can add a layer for all counties spapes, taken from the [Census 2000 shapefile](http://www.census.gov/geo/www/cob/co2000.html#shp).

	svgmap.py country USA -o USA.svg
	svgmap.py layer USA.svg census2000/co99_d00.shp -o USA-counties.svg

![United States with all counties](https://github.com/svgmap/svgmap.py/raw/master/doc/USA2.svg.png)

Command-specific parameters are:

* **--layer-id** will be used as id for the layer
* **--crop-to-layer** can be used to crop the shape to any existing layer

## Advanced usage 

### Quality

The quality level will be used to compute the parameter for the polygon simplification (also called *generalization*). The higher the quality, the less the polygons are simplified. A quality of 100 means no simplification. Note that the overall quality also depends on the output size.

![different qualities](https://github.com/svgmap/svgmap.py/raw/master/doc/quality.png)

### Joining regions

In some exceptional cases, the map data provided by Natural Earth admin-1 regions is too detailed. For instance, the following image shows the regions available for the United Kingdom. 

Fortunately, in those cases the Natural Earth adm1 shapefile stores some values that identify the "parent" region. We can use this data to join regions. By now, there's a CSV file named *data/region_joins.csv* that stores a list of all regions that should be joined. You can activate region joining by setting the **--join-regions** (**-j**) parameter.

	svgmap.py regions GBR --join-regions

![United Kingdom regions](https://github.com/svgmap/svgmap.py/raw/master/doc/GBR-regions.png)   ![United Kingdom regions](https://github.com/svgmap/svgmap.py/raw/master/doc/GBR-regions-joined.png)