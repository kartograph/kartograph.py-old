# Step by Step Installation Instructions
Tested on Mac OS 10.6.8

## Install Python 2.7 
http://python.org/download/

## Install needed libraries
### shapefile (http://code.google.com/p/pyshp/)

One of the following should work

	sudo pypm install pyshp
	easy_install pyshp


### Polygon

Unfortunately, the original maintainer of this library has taken offline his site. But you still can download the Mac package from here:

http://pypi.python.jp/Polygon/Polygon-2.0.4.macosx-10.6-universal.tar.gz#md5=302abdd94b25ccd5e3a7cbbd7635d777

and copy the folder "Polygon" into

/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/

### SvgFig
Follow instructions here:

http://code.google.com/p/svgfig/wiki/HowToInstall

## Download svgmap.py

	git clone https://github.com/svgmap/svgmap.py

Output should look like this:

	Cloning into svgmap.py...
	remote: Counting objects: 422, done.
	remote: Compressing objects: 100% (265/265), done.
	remote: Total 422 (delta 210), reused 353 (delta 141)
	Receiving objects: 100% (422/422), 38.82 MiB | 458 KiB/s, 	Resolving deltas: 100% (210/210), done.



## Download shapefiles
Kartograf needs some shapefiles.
http://kartograf.org/data.7z

Download them into your svgmap.py/ directory and unzip them via

	cd svmap.py
	7z x data.7z

You can safely replace any files.

You may need to install the **7z** archive utility

	brew install p7zip

## Test installation

	cd svgmap.py
	python svgmap world -o world.svg

If you want to open generated maps automatically, save the following script to /usr/local/bin/firefox

	#!/bin/sh
	open -a /Applications/Browser/Firefox.app $1

Using that, you're able to open things in Firefox via command line, eg.

firefox world.svg

If you then run svgmap without the -o parameter, the map would automatically open in firefox.

	python svgmap world

If you don't want to type that "python " prefix you can run

	chmod +x svgmap
	export PATH=$PATH:.
	svgmap world


