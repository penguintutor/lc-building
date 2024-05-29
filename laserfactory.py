# Laser Factory class
# Implements Factory Method Pattern using object classes

from laser import *

class LaserFactory:
    _etch_creators = {
        "line" : EtchLine,
        "rect" : EtchRect,
        "polygon" : EtchPolygon
        }
    
    _cut_creators = {
        "line" : CutLine,
        "rect" : CutRect,
        "polygon" : CutPolygon
        }
        
    @staticmethod
    def create_etch(type, args):
        creator = LaserFactory._etch_creators[type]
        return creator(*args)
    
    
    @staticmethod
    def create_cut(type, args):
        creator = LaserFactory._cut_creators[type]
        return creator(*args)