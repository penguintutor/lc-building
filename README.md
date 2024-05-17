# lc-building
LaserCut Model Building Creation Tool

## Important note
This is in a very early development stage. It has very limited functionality.
More details will be provided as the code is developed further.


## Prerequisites
Module Python svgwrite

On Debian / Ubuntu use

    sudo apt install python3-svgwrite
    
    
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
When creating templates it may be simpler to allow overlapping etches. 
For example shed hinges that overlap with the texture. In this case
it will need to be handled appropriately in the laser burn software
(eg. Lightburn weld feature), or through edit in Inkscape

Alternatively templates can be manually created that create all 
etches as polygons to avoid that problem.