# lc-building
LaserCut Model Building Creation Tool

## Important note
This is in a very early development stage. It has very limited functionality.
More details will be provided as the code is developed further.


## Prerequisites
Module Python svgwrite

On Debian / Ubuntu use

    sudo apt install python3-svgwrite
    
Module Python Shapely

    sudo apt install python3-shapely
    
    
## Running the code
Currently configs are all in the lcmake.py file
After setting appropriate dimensions run

    python3 lcmake.py 
    
   
## Development tests
There are some limited tests provided.
Tests are written using unittest

Run using:

    python3 -m unittest tests
or

    python3 tests.py
    
## Limitations

### Everything in mm
All measurements should be based on mm of actual size.
Conversation to scale mm and then to pixels is done within the
application. It may be possible to add an interface to allow 
other units (eg. inches) to be used as an input, but they will
still be handled internally as mm.

### Overlapping etches
Some lightburning software do not allow overlapping etches.
In the case of lightburn they will not output any parts that overlap.
This is a limitation of the lightburning software rather than this 
program.

It is recommended that you allow overlaps within this software and
then use the appropriate feature in the laser burning software. 
For example in lightburn you will need to use the weld feature, or
you could edit in Inkscape. 

When creating templates it is much simpler to allow overlapping etches. 
Particularly when different scales can produce rounding errors when scaling
is applied.
For example shed hinges that overlap with the texture. It also helps with
etches that are padded into polygons as otherwise those would need to be
taken into consideration.

### Limitations of small scales
Small scales (smaller than HO/OO) may have problems when dealing with small
size shapes. These may need to be edit in Inkscape before burning, or choose
a "N friendly" template
