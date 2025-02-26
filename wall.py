# Wall class with subclasses
# A wall is something that is cut out which could be a wall or a roof
# Can have texures applied or features added

# Create using actual dimensions in mm, then many of the methods return scaled dimensions
import math
from texture import *
from feature import *
from interlocking import Interlocking
from laser import *
from helpers import *
from shapely import Polygon
import json

# Texture is generated as part of get_etch,
# This means that if a feature is added as long as it
# is before get etch, then that part will be removed from
# the etch

# Textures are currently created in walls - may make sense to pull this into a
# separate texture generator class in future

# Interlocking is applied to sides that it is associated with.
# Interlocking starts at bottom left and works along the line
# As such all lines need to be in direction away from bottom left

# Note that methods ending _towall should only be used during a load or where update is being called afterwards
# Is used internally and for performance reasons can be used by file load etc.

# Some methods include option update=True
# Can instead set to False if multiple operations then apply manuall afterwards

class Wall():
    
    settings = {}
    
    def __init__ (self, name, points, view="front", position=[0,0]):
        # type is set as a wall - but allows us to check as may have different type
        # in future (eg. "exterior_object" - which could be porch support or something similar)
        self.type = "wall"
        self.name = name
        self.points = points
        #self.polygon = Polygon(points)
        self.view = view          # Which side to view it on when in the GUI
        self.position = position  # position within GUI scenes
        #print (f"Position {self.position}")
        #self.max_width = width
        #self.max_height = height
        self.show_interlock = False # Do we show interlocking - set using update
        self.show_textures = True # Do we show textures - set using update
        self.material = "smooth"
        self.il = []              # Interlocking - only one allowed per edge, but multiple allowed on a wall
        self.textures = []        # Typically one texture per wall, but can have multiple if zones used - must not overlap
        self.features = []        # Features for this wall
        self.history = []
        # by default are a wall, or could be roof - in future wall & roof are same
        # type will likely be used for different ways of creating a wall (eg. rectangle vs apex)
        #self.type = "wall"
        # Move these to variables so that they are cached within the wall class
        # Only update when update_xxx is called
        # These are for all features and textures - can get separately using get_wall_cuts / etches etc.
        # Which will generate as needed rather than for the whole object
        # Split into dictionaries to allow different views - eg. il / no_il (for interlock / no interlock)
        # Typically return (walls OR il) AND features AND ?textures
        self.cut_lines = {
            'wall': [],
            'il': [],
            'features': [],
            'textures': []
            }
        # basic etches is etches but without the exclusions
        # useful for editscene where features move position
        self.basic_etches = {
            'wall' : [],
            'il': [],
            'features': [],
            'textures': []
            }
        self.etches = {
            'wall' : [],
            'il': [],
            'features': [],
            'textures': []
            }
        self.outers = {
            'wall' : [],
            'il': [],
            'features': [],
            'textures': []
            }
        self.update()
        
    def __str__(self):
        return f"Wall: {self.name}"
    
    def get_summary (self):
        return f"{self.type} - {self.name}"
    
    # Returns summary of wall as a dictionary
    def get_summary_dict(self):
        summary_dict = {
            "Name": self.name,
            "Type": self.type,
            "Size": self.get_size_string()
            }
        # Add one line for each texture applied
        for i in range (0, len(self.textures)):
            summary_dict[f"Texture {i+1}"] = self.textures[i].style
        # Add one line for each feature
        for i in range (0, len(self.features)):
            summary_dict[f"Feature {i+1}"] = self.features[i].get_summary()
        return summary_dict
        
    # get a list of edges
    def get_edges_str (self):
        edges = []
        for i in range (0, len(self.points)):
            # if it's not the first then append current point to previous entry
            if i != 0 :
                edges[i-1] = f"{edges[i-1]}{int(self.points[i][0])} , {int(self.points[i][1])}"
            # skip last one (after adding to the end of previous one) as it's back to start
            # Create next entry (but don't put future point)
            if i < len(self.points)-1:
                edges.append (f"Edge {i+1}: {int(self.points[i][0])} , {int(self.points[i][1])} : ")
        return edges
            
        
    def get_features (self):
        return self.features
    
    def get_textures (self):
        return self.textures
    
    # Provides summary of wall for save
    # Also need to get any textures, interlocking and features separately
    def get_save_data (self):
        return [self.name, self.points, self.view, self.position]
    
    def get_save_textures (self, wall_num):
        save_textures = []
        for texture in self.textures:
            save_textures.append({
                "type" : texture.style,
                "wall" : wall_num,
                "settings": texture.settings
                })
        return save_textures
    
    # Todo - convert cuts, outers and etches to list forma
    def get_save_features (self, wall_num):
        save_features = []
        for feature in self.features:
            save_features.append({
                "type": feature.type,
                "template": feature.template,
                "wall": wall_num,
                "parameters": {
                    "pos": [feature.min_x, feature.min_y],
                    "exclude": feature.points
                    },
                "cuts": feature.cuts_as_list(),
                "etches": feature.etches_as_list(),
                "outers": feature.outers_as_list()
                })
        return save_features

    # Normally use absolute position rather than relative as that is
    # what we get from the viewscene
    def move_pos(self, pos):
        # only add to history if changed
        if self.position != pos:
            self.history.append(["move", self.position])
            self.position = pos

    def move_rel(self, pos):
        # Store current position in history
        self.history.append(["move", self.position])
        self.position[0] += pos[0]
        self.position[1] += pos[1]
        

    # Align a feature against the wall
    # Uses current wall and moves feature
    def wall_feature_align (self, direction, feature):
        # left or top are simplist as just set to 0
        if direction == 'left':
            feature.min_x = 0
        elif direction == 'top':
            feature.min_y = 0
        # for bottom and right then offset based on size of wall and feature
        elif direction == 'right':
            feature.min_x = self.get_maxwidth() - feature.get_maxwidth()
        elif direction == 'bottom':
            feature.min_y = self.get_maxheight() - feature.get_maxheight()
        # for middle and centre use 1/2 wall and 1/2 feature
        elif direction == 'centre':
            feature.min_x = (self.get_maxwidth()/2) - (feature.get_maxwidth()/2)
        elif direction == 'middle':
            feature.min_y = (self.get_maxheight()/2) - (feature.get_maxheight()/2)
        feature.update_pos()

    # Updates cuts, etches and outers
    # Interlock = None, keep current, otherwise update
    # Interlock and texture no longer used - instead use through get edges etc.
    # quick is faster, but not as accurate
    # for export always used a quick=False
    def update (self):
        self.update_cuts()
        #print ("Updating etches")
        self.update_etches()
        #print ("Etches updated")
        #self.update_exclude()
        self.update_outers()

        
    def update_exclude(self):
        pass
        
    # Gets wall edges - not including interlocking
    def get_wall_edges (self):
        cut_edges = []
        # Start at 1 (2nd point) end of first edge
        # as reference previous in the for loop
        for i in range(1, len(self.points)):
            cut_edges.append([self.points[i-1], self.points[i]])
        return cut_edges

    def edges_to_lines (self, edges):
        lines = []
        for edge in edges:
            lines.append(CutLine(cut_edges[i][0], cut_edges[i][1]))
        return lines
            
    # Get wall edges with interlocking applied
    def get_il_edges (self):
        il_edges = []
        cut_edges = self.get_wall_edges()
        for i in range(0, len(cut_edges)):
            # Do any interlocks apply to this edge if so apply interlocks
            # copy edge into list for applying transformations
            this_edge_segments = [cut_edges[i]]
            start_line = this_edge_segments[0][0]
            end_line = this_edge_segments[0][1]
            edge_ils = None
            
            for il in self.il:
                if il.get_edge() == i:
                    # add interlocks to this edge
                    edge_ils = il
                    
            # Now sort into order to apply
            # Must not overlap, but only check startpos rather than end
            # Note if interlock = false then we don't have added any edge_ils so don't need to check here
            if edge_ils != None:
                # remove last segment to perform transformations on it
                remaining_edge_segment = this_edge_segments.pop()
                # Then add any returned segments back onto the list
                this_edge_segments.extend(edge_ils.add_interlock_line(start_line, end_line, remaining_edge_segment))
                il_edges.extend(this_edge_segments)
            else:
                il_edges.append(cut_edges[i])
        return il_edges
        
    # Convert edges into line objects
    def edges_to_lines (self, edges):
        lines = []
        for this_edge in edges:
            lines.append(CutLine(this_edge[0], this_edge[1]))
        return lines
            
    # Gets only cuts associated with the wall itself (not features / textures)
    # Used by wall edit where need separate from features
    def get_wall_cuts (self, show_interlock=False, show_textures=False):
        # Is interlocking turned on?
        # If not then get without, if it is then get with
        # Start at 1 (2nd point) end of first edge
        if (show_interlock == False):
            return self.cut_lines['wall']
        #print (f"get wall cuts return il {self.cut_lines['il']}")
        # with interlocking
        return self.cut_lines['il']
        
                

    # Generate all the cuts and store in self.cuts
    # For performance reasons call this initially then just use get_cuts
    # but if update then run this again before running get_cuts
    def update_cuts (self):
        wall_edges = self.get_wall_edges ()
        self.cut_lines['wall']=self.edges_to_lines(wall_edges)
        il_edges = self.get_il_edges ()
        self.cut_lines['il']=self.edges_to_lines(il_edges)
        # Add cuts from features 
        self.cut_lines['features'] = self._get_cuts_features()
        

    # Get cuts for outside of wall and any inner cuts (eg. features)
    # Although don't have textures with cuts included for consistancy with edges
    # show_textures does nothing
    def get_cuts (self, show_interlock=False, show_textures=False):
        # Note uses copy to prevent merging features into cut_lines multiple times
        if (show_interlock == False):
            cut_lines = copy.copy(self.cut_lines['wall'])
        else:
            cut_lines = copy.copy(self.cut_lines['il'])
        # Add features
        cut_lines.extend(self.cut_lines['features'])
        # Add textures
        if show_textures == True:
            cut_lines.extend(self.cut_lines['textures'])
        return cut_lines
    
    def get_etches (self, show_interlock=False, show_textures=False):
        # Note uses copy to prevent merging features into cut_lines multiple times
        # Wall elements most likely empty, but copy anyway in case
        if (self.show_interlock == False):
            etches = copy.copy(self.etches['wall'])
        else:
            etches = copy.copy(self.etches['il'])
        # Add features
        etches.extend(self.etches['features'])
        # Add textures
        if show_textures == True:
            etches.extend(self.etches['textures'])
        return etches
    

    # Returns texture but without excluding features
    # Used by edit scene for performance reasons
    def get_texture_etches_basic (self):
        return self.basic_etches['textures']

    def get_texture_etches (self):
        return self.etches['textures']
    
    def update_etches (self):
        # Although we have etches for wall - nothing to do in this version
        self.basic_etches['textures'] = self._texture_to_etches()
        self.etches['textures'] = self._texture_remove_features()
        # Add etches from features
        self.etches['features'] = self._get_etches_features()

    def get_outers (self, show_interlock=False, show_textures=False):
        # Note uses copy to prevent merging features into cut_lines multiple times
        # Wall elements most likely empty, but copy anyway in case
        if (self.show_interlock == False):
            outers = copy.copy(self.outers['wall'])
        else:
            outers = copy.copy(self.outers['il'])
        # Add features
        outers.extend(self.outers['features'])
        # Add textures
        if show_textures == True:
            outers.extend(self.outers['textures'])
        return outers
        
    def update_outers (self):
        # Add any accessories (windows etc.)
        for feature in self.features:
            self.outers['features'].extend(feature.get_outers())
    
    def get_type (self):
        return self.type
    
    def get_size_string (self):
        return (f"{int(self.get_maxwidth()):,d}mm x {int(self.get_maxheight()):,d}mm")
    
    def get_maxsize (self):
        return (self.get_maxwidth(), self.get_maxheight())
    
    # max distance x
    def get_maxwidth (self):
        polygon = Polygon(self.points)
        return polygon.bounds[2] - polygon.bounds[0]
    
    def get_maxheight (self):
        polygon = Polygon(self.points)
        return polygon.bounds[3] - polygon.bounds[1]


    # Used by builder class or internally within this
    # Does not update etches
    def add_texture_towall (self, type, area, settings):
        # If no area / zone provided then use wall
        if area == []:
            area = self.points
        # reordered here when passed to constructor
        self.textures.append(Texture(area, type, settings))
        
    # Note that this is different order to texture constructor as
    # in constructor type is optional - but not in here
    # area can be [] which means entire wall
    def add_texture (self, type, area, settings, update=True):
        self.add_texture_towall (type, area, settings)
        if update == True:
            # Only update etches as that is limit of textures
            self.update_etches()

    # This is internal method - or one to be used when loading from file
    # Does not perform update - also used by add_feature but then performs update
    # If using this then must perform update after loading
    def add_feature_towall (self, feature_type, feature_template, startpos, points, cuts=None, etches=None, outers=None):
        # feature number will be next number
        # Will return that assuming that this is successful
        feature_num = len(self.features)
        if cuts == None:
            cuts = []
        if etches == None:
            etches = []
        if outers == None:
            outers = []
        self.features.append(Feature(feature_type, feature_template, startpos, points, cuts, etches, outers))
        return feature_num
    
    # Delete a feature by id
    def del_feature (self, feature_num):
        del self.features[feature_num]
        
    # delete feature by obj
    def del_feature_obj (self, obj):
        for i in range (0, len(self.features)):
            if self.features[i] == obj:
                del self.features[i]    

    # Add a feature - such as a window
    # cuts, etches and outers should all be lists
    # If not set to None then change to [] avoid dangerous default
    def add_feature (self, feature_type, feature_template, startpos, points, cuts=None, etches=None, outers=None, update=True):
        feature_num = self.add_feature_towall (feature_type, feature_template, startpos, points, cuts, etches, outers)
        if update == True:
            self.update()
        return feature_num

    # Add feature loaded from file
    def add_feature_file (self, filename):
        # Keep reference to filename loaded
        try:
            with open(filename, 'r') as datafile:
                feature_data = json.load(datafile)
        except Exception as err:
            print (f"Error {err}")
            return
        # Simple check did we get a name
        if 'name' not in feature_data.keys():
            print ("Invalid feature file")
            return
        # Create feature object
        # set pos to be near top left - then can be moved by user
        pos = (50, 50)
        # if exclude not set then calculate from width and height
        if "exclude" in feature_data.keys():
            points = feature_data['exclude']
        else:
            width = feature_data['parameters']['width']
            height = feature_data['parameters']['height']
            points = [
                [0,0],
                [width,0],
                [width, height],
                [0, height],
                [0,0]
                ]
                
        self.add_feature (feature_data["type"], feature_data["template"], pos, points, feature_data['cuts'], feature_data['etches'], feature_data['outers'])
        # Send signal to editscene to refresh


    # add any interlock rules for the edges
    # edges are number from 0 (top left) in clockwise direction
    # parameters should be a dictionary if supplied
    def add_interlocking (self, step, edge, primary, reverse, il_type, parameters=None):
        #print (f"Adding interlocking to {self.name}, Edge {edge}, Step {step}, {primary}, {reverse}, {il_type}, Params {parameters}")
        if parameters==None:
            parameters = {}
        self.il.append(Interlocking(step, edge, primary, reverse, il_type, parameters))
        return self.il[-1]
            
    def _texture_remove_features(self):
        #print ("Removing features")
        exclude_areas = []
        #update_lines = []
        for feature in self.features:
            exclude_areas.append(feature.get_points())
        update_lines = line_remove_features(self.basic_etches['textures'], exclude_areas)
        return update_lines
            
    # This is later stage in get_etches
    def _texture_to_etches(self):
        etches = []
        #print ("Texture to etches")
        #print (f"Self textures {self.textures}")
        for texture in self.textures:
            #print (f"Getting this texture {texture}")
            # Each texture can have one or more etches
            etches.extend(texture.get_etches())
        return etches
        

    def _get_cuts_features (self):
        feature_cuts = []
        for feature in self.features: 
            feature_cuts.extend(feature.get_cuts())
            if "outertype" in self.settings and self.settings["outertype"] == "cuts":
                new_cuts = feature.get_outers_cuts()
                if new_cuts != None:
                    feature_cuts.extend(new_cuts)
        return feature_cuts
    
    def _get_etches_features (self):
        feature_etches = []
        for feature in self.features:
            #print (f"Feature {feature}")
            feature_etches.extend(feature.get_etches())
            if "outertype" in self.settings and self.settings["outertype"] == "etches":
                #print (f"Getting outers from _get_etches")
                new_etches = feature.get_outers_etches()
                if new_etches != None and new_etches != []:
                    feature_etches.extend(new_etches)
        #print (f"Returning from _get_etches_features {feature_etches}")
        return feature_etches


    # Delete interlock on an edge
    # as stated only one interlock should be applied to an edge, but delete any that reference this edge.
    def delete_il (self, edge):
        for this_il in self.il:
            if this_il.edge == edge:
                self.il.remove(this_il)
    
    # If size has changed then may need to update texture points
    def update_texture_points(self):
        for texture in self.textures:
            if texture.fullwall:
                texture.change_points(self.points)