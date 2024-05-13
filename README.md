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
Tests are written using unittest
Run using:

    python3 -m unittest tests
or
    python3 tests.py