import unittest
from wall import *
from scale import *

class TestWall(unittest.TestCase):
    
    def test_wall_add(self):
        # Test parameters
        depth = 1826
        height = 1864
        test_wall = RectWall(depth, height)
        cuts = test_wall.get_cuts()
        self.assertEqual(cuts[0][0], "rect")
        self.assertEqual(cuts[0][2][0], depth)
        self.assertEqual(cuts[0][2][1], height)
        
    def test_wall_maxsize(self):
        depth = 1826
        height = 1864
        test_wall = RectWall(depth, height)
        max_size = test_wall.get_maxsize()
        self.assertEqual(max_size[0], depth)
        self.assertEqual(max_size[1], height)
        
class TestScale(unittest.TestCase):

    def test_get_scales(self):
        sc = Scale()
        list_scales = sc.get_scales()
        self.assertTrue('OO' in list_scales)
        self.assertFalse('invalid' in list_scales)
        
    def test_scale_convert(self):
        sc = Scale()
        # Test with default 'OO'
        # Test based on rounded number
        self.assertEqual(round(sc.scale_convert(2000)), 26)
        # Change to G scale
        sc.set_scale('G')
        self.assertEqual(round(sc.scale_convert(2000)), 89)
        # Change back to OO - ensure same
        sc.set_scale('OO')
        self.assertEqual(round(sc.scale_convert(2000)), 26)
        
    def test_mm_to_pixels(self):
        sc = Scale()
        self.assertEqual(round(sc.mm_to_pixel(89)), 315)
        # Change scale - should not change value
        sc.set_scale('N')
        self.assertEqual(round(sc.mm_to_pixel(89)), 315)
        
    # Use single value
    def test_convert_single(self):
        # start with different scale on constructor
        sc = Scale('N')
        self.assertEqual(round(sc.convert(2000)), 48)
        # Change scale
        sc.set_scale('OO')
        self.assertEqual(round(sc.convert(2000)), 93)
        
    def test_convert_list(self):
        # start with different scale on constructor
        sc = Scale('N')
        scaled_values = sc.convert([2000, 1000])
        self.assertEqual(round(scaled_values[0]), 48)
        self.assertEqual(round(scaled_values[1]), 24)
        # Change scale
        sc.set_scale('OO')
        # Use tuples
        scaled_values = sc.convert((2000, 1000))
        self.assertEqual(round(scaled_values[0]), 93)
        self.assertEqual(round(scaled_values[1]), 47)
    
if __name__ == '__main__':
    unittest.main()