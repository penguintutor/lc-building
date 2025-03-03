from helpers import *

class Interlocking():
    
    # Use class variable for material_thickness
    # set once then use for all interlocking calculations
    material_thickness = 0
    
    # Note parameters if supplied should be a dictionary
    def __init__ (self, step, edge, primary, reverse="", il_type="default", parameters=None):
        # Type is not used at the moment, but allows for different configs in future
        self.il_type = il_type
        self.step = step         # Size of a single interlock step
        self.edge = edge         # Edge number on wall this is contained in
        self.primary = primary   # Is this "primary" or "secondary"
        self.reverse = False
        if reverse == "reverse" or reverse == 1:   # Set to "reverse" to reverse direction
            self.reverse = True
        self.parameters = {}
        if parameters != None:
            self.parameters = parameters         # Any additional settings
        # get start position (0 if not defined)
        # also used to sort
        # note should never have multiple interlocking objects
        # on the same edge that overlap
        self.start = 0
        self.end = None
        if "start" in self.parameters.keys():
            self.start = self.parameters["start"]
        # If end is 0 then it's default so ignore
        if "end" in self.parameters.keys() and self.parameters["end"] != 0:
            self.end = self.parameters["end"]
        
    def __str__ (self):
        return (f"Edge {self.edge}, Step {self.step}, Primary {self.primary}, Reverse {self.reverse}, {self.parameters}")
        
    # sort based on start parameter
    def __lt__(self, other):
        return self.start < other.start
    
    def is_primary (self):
        return self.primary == "primary"
        
    # Takes a single line segment (either full line or remaining after an interlock has been added)
    # then add the interlocks recursively through add_interlock_segment
    # returns list of line segments for the interlocking and any remaining edge
    # line start is the start of the entire line (used for determining start and end)
    def add_interlock_line (self, line_start, line_end, line):
        # if this is secondary then we need to reverse the direction of the line
        # note if we wanted to put this back to a polygon we would need to reverse the
        # direction of the returned segments, but not neccessary if using lines which
        # if what we are doing here (also need to invert direction of tabs
        
        # If not primary and not reverse then reverse direction of entire line then treat the same
        # also if secondary and not reverse
        if (self.primary == "primary" and self.reverse == True) or (self.primary != "primary" and self.reverse != True) :
            line_start = line_end
            rev_line = [line[1],line[0]]
            line = rev_line
        
        # Get length of line from original to end of last segment
        line_dist = get_distance (line_start, line[1])
        # If there is end and less then line_dist then use that instead
        if self.end != None and self.end < line_dist:
            line_dist = self.end
        new_segments = []
        # Only ever work on the remaining part of the line
        # Determine angle
        angle = get_angle (line)
        # Set first position based on line start and adding space
        # if start defind then that should be starting point (if not already passed)
        # if not then add space for a step before we start the next segment
        if self.start != 0:
            # If not already passed self.start then use that
            if (get_distance (line_start, line[0]) < self.start):
                # set start as next segment
                newpos = add_distance_to_points (line_start, self.start, angle)
                #Create new segment to this position
                new_segments.append((line[0], newpos))
                # Update start on current_segment
                #current_segment_start = newpos
                new_line = (newpos, line[1])
            # Otherwise use current line
            else:
                new_line = line
        else:
            # If no start add self.step
            # get new x,y
            newpos = add_distance_to_points (line[0], self.step, angle)
            if check_distance (line_start, newpos, line_dist) < 1:
                # not enough space add last segment to new segments and return
                ###print (f"Adding line {line}")
                new_segments.append(line)
                return new_segments
            # Add to new segments
            new_segments.append((line[0], newpos))
            new_line = (newpos, line[1])
        
        # Now can start adding segments
        # call recursively 
        # remove the last segment and replace with current segment
        new_segments.extend(self.add_interlock_segment(line_start, new_line, line_dist))
        # Check we have at least enough space for this segment, plus one more segment
        
        # return as list of segments
        return new_segments
       

    # max line should be last distance for line (eg. - 1 step from end)
    def add_interlock_segment (self, line_start, line, max_line):
        #print (f" Adding segment {line_start} {line} {max_line}")
        new_segments = [] 
        # Check we have enough space for Indent 
        angle = get_angle (line)
        # Next tab is 2 x tab position and will be where the next tab starts if applicable (not this tab)
        nexttab = add_distance_to_points (line[0], self.step * 2, angle)
        if check_distance (line_start, nexttab, max_line) < 0:
            return [line]
        endtab = add_distance_to_points (line[0], self.step, angle)
        # confirmed we have space so add next segment - turn by +/-90 degrees
        if self.reverse != True:
            seg_angle = angle+90
        else:
            seg_angle = angle-90
        starttab = add_distance_to_points (line[0], Interlocking.material_thickness, seg_angle)
        new_segments.append((line[0], starttab))
        # next segment is back to normal angle
        toptab = add_distance_to_points (starttab, self.step, angle)
        new_segments.append((starttab, toptab))
        # Now back to endtab already calculated
        new_segments.append((toptab, endtab))
        # Straight line to start of next tab
        new_segments.append((endtab, nexttab))
        # now call again with next step
        new_segments.extend(self.add_interlock_segment (line_start, (nexttab, line[1]), max_line))
        return new_segments

    
    # are new positions passed the end of the line
    #replaced by _reached_end which looks at distance from start
    # check that neither of these are beyond the end of the line (if so just return this)
    # Need to check based on the direction as may be negative direction
    def _reached_end_xy (self, line, newpoints):
        newstartx = newpoints[0]
        newstarty = newpoints[1]
        # If line in +x direction
        if (line[0][0] <= line[1][0]):
            if newstartx > line[1][0]:
                return True
        else:
            if newstartx < line[1][0]:
                return True
        # if line in +y direction
        if (line[0][1] <= line[1][1]):
            if newstarty >= line[1][1]:
                return True
        else:
            if newstarty < line[1][1]:
                return True
        return False
    
    def get_edge (self):
        return self.edge
    
    
