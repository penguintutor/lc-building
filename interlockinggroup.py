# Used to track combination of Interlocking Primary and Secondary entries

# _wall = wall_id
# _il = Interlocking object
class InterlockingGroup():
    def __init__ (self, primary_wall, primary_il, secondary_wall, secondary_il):
        self.primary_wall = primary_wall
        self.primary_il = primary_il
        self.secondary_wall = secondary_wall
        self.secondary_il = secondary_il
        
    

        