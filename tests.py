import unittest
from wall import *
from scale import *
from laser import *
from buildingtemplate import *
from featuretemplate import *

class TestWall(unittest.TestCase):
    
    def test_wall_add(self):
        # Test parameters
        depth = 1826
        height = 1864
        test_wall = RectWall(depth, height)
        cutsobj = test_wall.get_cuts()
        cuts = cutsobj[0].get_cut()
        self.assertEqual(cuts[0], "rect")
        self.assertEqual(cuts[2][0], depth)
        self.assertEqual(cuts[2][1], height)
        
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
        self.assertEqual(round(sc.mm_to_pixel(89)), 338)
        # Change scale - should not change value
        sc.set_scale('N')
        self.assertEqual(round(sc.mm_to_pixel(89)), 338)
        
    # Use single value
    def test_convert_single(self):
        # start with different scale on constructor
        sc = Scale('N')
        self.assertEqual(round(sc.convert(2000)), 51)
        # Change scale
        sc.set_scale('OO')
        self.assertEqual(round(sc.convert(2000)), 100)
        
    def test_convert_list(self):
        # start with different scale on constructor
        sc = Scale('N')
        scaled_values = sc.convert([2000, 1000])
        self.assertEqual(round(scaled_values[0]), 51)
        self.assertEqual(round(scaled_values[1]), 26)
        # Change scale
        sc.set_scale('OO')
        # Use tuples
        scaled_values = sc.convert((2000, 1000))
        self.assertEqual(round(scaled_values[0]), 100)
        self.assertEqual(round(scaled_values[1]), 50)
        
        
# Based on example template - test loading file etc.
class TestTemplate(unittest.TestCase):   
    
    def test_load_file(self):
        filename = "templates/building_shed_apex_1.json"
        template = BuildingTemplate()
        template.load_template (filename)
        data = template.get_data()
        # Text some particular values
        self.assertEqual(data["name"], "Apex shed")
        self.assertEqual(data["defaults"]["depth"], 1826)
        self.assertEqual(data["typical"]["wood_height"], 150)
        self.assertEqual(data["walls"][0][0], "ApexWall")
        self.assertEqual(data["roofs"][0], "ApexRoof")
        self.assertEqual(data["options"][0], "door_shed_1")
        self.assertEqual(data["options"][1], "window_shed_1")
        
    def test_feature_window(self):
        filename = "templates/window_shed_1.json"
        template = FeatureTemplate()
        template.load_template (filename)
        data = template.get_data()
        self.assertEqual(data["type"], "Window")
        self.assertEqual(data["defaults"]["width"], 400)
        self.assertEqual(data["cuts"][0][0], "rect")
        
        
    def test_feature_window_cuts(self):
        filename = "templates/window_shed_1.json"
        template = FeatureTemplate()
        template.load_template (filename)
        cuts = template.get_cuts()
        self.assertEqual(cuts[0][0], "rect")
        
        
    # Test parsing of strings
    def test_token_process_1(self):
        filename = "templates/window_shed_1.json"
        template = FeatureTemplate()
        template.load_template (filename)
        test_string = "x+3"
        output_string = template.process_token_str(test_string)
        self.assertEqual(output_string, "0+3")
        output = template.process_token(test_string)
        self.assertEqual(output, 3)
        test_string = "y"
        output_string = template.process_token_str(test_string)
        self.assertEqual(output_string, "0")
        output = template.process_token(test_string)
        self.assertEqual(output, 0)
        test_string = "((7+x+width/2))"
        output_string = template.process_token_str(test_string)
        self.assertEqual(output_string, "((7+0+400/2))")
        output = template.process_token(test_string)
        self.assertEqual(output, 207.0)
    
    
if __name__ == '__main__':
    unittest.main()