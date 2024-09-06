import unittest
from wall import *
from scale import *
from laser import *
from buildingdata import *
from buildingtemplate import *
from featuretemplate import *
from interlocking import *
from helpers import *
from texture import *
from config import LCConfig
from builder import Builder

# Test loading of config values
# Just few example values tested
class TestConfig(unittest.TestCase):
    # May need to update if changing configuration - these are default settings
    def test_config_read(self):
        self.config = LCConfig()
        self.assertEqual(self.config.stroke_width, 1)
        self.assertEqual(self.config.etch_strokes[0][1], 0)

class TestWall(unittest.TestCase):
    
    def test_wall_add(self):
        # Test parameters
        depth = 1826
        height = 1864
        test_wall = Wall("Wall test add", [(0,0),(depth,0),(depth,height),(0,height),(0,0)])
        cuts = test_wall.get_cuts()
        self.assertEqual(cuts[0].get_type(), "line")
        
    def test_wall_maxsize(self):
        depth = 1826
        height = 1864
        test_wall = Wall("Wall test maxsize", [(0,0),(depth,0),(depth,height),(0,height),(0,0)])
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
## Note based on old template - needs to be updated when template is updated
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
        self.assertEqual(data["walls"][0][0], "WallApex")
        self.assertEqual(data["roofs"][0][0], "RoofApexLeft")
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
    
    
# Interlocking is based on lines in clockwise direction
# Primary go outwards from start to end
# Secondary to inwards from end to start
class TestInterlocking(unittest.TestCase):   
    
        
    def test_line_interlocking_primary_1(self):
        # Primary so start at beginning of line
        Interlocking.material_thickness = 10
        il = Interlocking (100, 1, "primary")
        # Vertical line from bottom to top
        line = [(0,1000), (0, 0)]
        # Appears that this is repeating args - but the line could actually be a segment
        # of a longer line
        segments = il.add_interlock_line (line[0], line[1], line)
        expected_output = [((0, 1000), (0, 900)), ((0, 900), (-10, 900)), ((-10, 900), (-10, 800)), ((-10, 800), (0, 800)), ((0, 800), (0, 700)), ((0, 700), (-10, 700)), ((-10, 700), (-10, 600)), ((-10, 600), (0, 600)), ((0, 600), (0, 500)), ((0, 500), (-10, 500)), ((-10, 500), (-10, 400)), ((-10, 400), (0, 400)), ((0, 400), (0, 300)), ((0, 300), (-10, 300)), ((-10, 300), (-10, 200)), ((-10, 200), (0, 200)), ((0, 200), (0, 100)), ((0, 100), (0, 0))]
        self.assertEqual(segments, expected_output)
        
    def test_line_interlocking_secondary_1(self):
        # Secondary so start at end of line
        il = Interlocking (100, 1, "secondary")
        Interlocking.material_thickness = 20
        # Vertical line from top to bottom
        line = [(100, 0), (100, 1000)]
        # Appears that this is repeating args - but the line could actually be a segment
        # of a longer line
        segments = il.add_interlock_line (line[0], line[1], line)
        expected_output = [((100, 1000), (100, 900)), ((100, 900), (80, 900)), ((80, 900), (80, 800)), ((80, 800), (100, 800)), ((100, 800), (100, 700)), ((100, 700), (80, 700)), ((80, 700), (80, 600)), ((80, 600), (100, 600)), ((100, 600), (100, 500)), ((100, 500), (80, 500)), ((80, 500), (80, 400)), ((80, 400), (100, 400)), ((100, 400), (100, 300)), ((100, 300), (80, 300)), ((80, 300), (80, 200)), ((80, 200), (100, 200)), ((100, 200), (100, 100)), ((100, 100), (100, 0))]
        self.assertEqual(segments, expected_output)
        
    # Horizontal line
    def test_line_horizontal_primary_1(self):
        Interlocking.material_thickness = 8
        # Primary so start at beginning of line
        il = Interlocking (10, 1, "primary")
        # From left to right
        line = [(0,0), (60, 0)]
        # Appears that this is repeating args - but the line could actually be a segment
        # of a longer line
        segments = il.add_interlock_line (line[0], line[1], line)
        expected_output = [((0, 0), (10, 0)), ((10, 0), (10, -8)), ((10, -8), (20, -8)), ((20, -8), (20, 0)), ((20, 0), (30, 0)), ((30, 0), (30, -8)), ((30, -8), (40, -8)), ((40, -8), (40, 0)), ((40, 0), (50, 0)), ((50, 0), (60, 0))]

        self.assertEqual(segments, expected_output)

# Texture
class TestTexture(unittest.TestCase):
    
    def test_horizontal_line_extend_right(self):
        depth = 200
        height = 180
        texture = Texture([(0,0),(depth,0),(depth,height),(0,height),(0,0)])
        lines = texture._line([1, 20],[2000,20])
        self.assertEqual (lines[0][0][0], 1)
        self.assertEqual (lines[0][0][1], 20)
        self.assertEqual (lines[0][1][0], 199)
        self.assertEqual (lines[0][1][1], 20)
        
    def test_horizontal_line_extend_left(self):
        depth = 200
        height = 180
        texture = Texture([(20,0),(depth,0),(depth,height),(20,height),(20,0)])
        lines = texture._line([1, 49],[100,49])
        self.assertEqual (lines[0][0][0], 21)
        self.assertEqual (lines[0][0][1], 49)
        self.assertEqual (lines[0][1][0], 100)
        self.assertEqual (lines[0][1][1], 49)

    def test_horizontal_line_inside(self):
        depth = 200
        height = 180
        texture = Texture([(0,0),(depth,0),(depth,height),(0,height),(0,0)])
        lines = texture._line([1, 1],[150, 1])
        self.assertEqual (lines[0][0][0], 1)
        self.assertEqual (lines[0][0][1], 1)
        self.assertEqual (lines[0][1][0], 150)
        self.assertEqual (lines[0][1][1], 1)

    def test_vertical_line_extend_above(self):
        depth = 200
        height = 180
        texture = Texture([(0,20),(depth,20),(depth,height+20),(0,height+20),(0,20)])
        lines = texture._line([1, 100],[1,5])
        self.assertEqual (lines[0][0][0], 1)
        self.assertEqual (lines[0][0][1], 100)
        self.assertEqual (lines[0][1][0], 1)
        self.assertEqual (lines[0][1][1], 21)

    def test_vertical_line_extend_below(self):
        depth = 200
        height = 180
        texture = Texture([(0,0),(depth,0),(depth,height),(0,height),(0,0)])
        lines = texture._line([41, 225],[41,100])
        self.assertEqual (lines[0][0][0], 41)
        self.assertEqual (lines[0][0][1], 179)
        self.assertEqual (lines[0][1][0], 41)
        self.assertEqual (lines[0][1][1], 100)

    def test_vertical_line_inside(self):
        depth = 200
        height = 180
        texture = Texture([(0,0),(depth,0),(depth,height),(0,height),(0,0)])
        lines = texture._line([150, 177],[150,10])
        self.assertEqual (lines[0][0][0], 150)
        self.assertEqual (lines[0][0][1], 177)
        self.assertEqual (lines[0][1][0], 150)
        self.assertEqual (lines[0][1][1], 10)


    def test_angle_line_both(self):
        depth = 200
        height = 200
        texture = Texture([(0,0),(depth,0),(depth,height),(0,height),(0,0)])
        lines = texture._line([100, 220],[220,100])
        self.assertEqual (lines[0][0][0], 121)
        self.assertEqual (lines[0][0][1], 199)
        self.assertEqual (lines[0][1][0], 199)
        self.assertEqual (lines[0][1][1], 121)


    # Tests line is split where interacting with edges of polygon
    def test_line_polygon_split(self):
        # Texture is two apex
        texture = Texture([(0,20),(20,0),(40,20),(60,0),(80,20),(80,120),(0,120), (0,20)])
        lines = texture._line([0, 10],[200,10])
        self.assertEqual (lines[0][0][0], 11)
        self.assertEqual (lines[0][0][1], 10)
        self.assertEqual (lines[0][1][0], 29)
        self.assertEqual (lines[0][1][1], 10)
        self.assertEqual (lines[1][0][0], 51)
        self.assertEqual (lines[1][0][1], 10)
        self.assertEqual (lines[1][1][0], 69)
        self.assertEqual (lines[1][1][1], 10)



    # Tests line is split where interacting with edges of polygon
    # 3 peaks
    def test_line_polygon_split_2(self):
        # Texture is 3 apex
        texture = Texture([(0,20),(20,0),(40,20),(60,0),(80,20),(100,0), (120,20),(120,120),(0,120), (0,20)])
        lines = texture._line([0, 10],[200,10])
        self.assertEqual (lines[0][0][0], 11)
        self.assertEqual (lines[0][0][1], 10)
        self.assertEqual (lines[0][1][0], 29)
        self.assertEqual (lines[0][1][1], 10)
        self.assertEqual (lines[1][0][0], 51)
        self.assertEqual (lines[1][0][1], 10)
        self.assertEqual (lines[1][1][0], 69)
        self.assertEqual (lines[1][1][1], 10)
        # Test for final section
        self.assertEqual (lines[2][0][0], 91)
        self.assertEqual (lines[2][0][1], 10)
        self.assertEqual (lines[2][1][0], 109)
        self.assertEqual (lines[2][1][1], 10)



# Test the Builder class - along with subclasses that are read
class TestBuilder(unittest.TestCase):
    # Read data file, write it out, read it in and compare
    def test_read_file(self):
        config = LCConfig()
        builder = Builder(config)
        builder.load_file("tests/building1.json")
        walls = builder.building.get_walls()
        # Take first entry and see if it's expected
        self.assertEqual (walls[0][0], 'Front with window')
        # Now save as a new file
        builder.save_file("tests/building1a.json")
        # Create new builder object load and compare
        builder1a = Builder(config)
        builder1a.load_file("tests/building1a.json")
        walls1a = builder1a.building.get_walls()
        # Take first entry and see if it's expected
        self.assertEqual (walls1a[0][0], 'Front with window')

# helper functions
class TestHelpers(unittest.TestCase):   
    
    def test_get_angles(self):
        # Horizontal line (left to right)
        angle = get_angle([[0, 0], [100, 0]])
        self.assertEqual(angle, 90)
        # Horizontal line (right to left)
        angle = get_angle([[50, 50], [0, 50]])
        self.assertEqual(angle, 270)
        # Vertical line upwards
        angle = get_angle([[200, 1000], [200, 100]])
        self.assertEqual(angle, 180)
        # Vertical line downwards
        angle = get_angle([[20, 20], [20, 200]])
        self.assertEqual(angle, 0)
     
        



        
if __name__ == '__main__':
    unittest.main()