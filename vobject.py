# Used to maintain association of images on GUI to which object in Builder class


class VObject():
    
    def __init__(self, scene, sceneobject, objecttype, objectnum):
        self.scene = scene              # Which scene it's on
        self.sceneobject = sceneobject  # Object number on scene 
        self.objecttype = objecttype    # Type of object (eg. wall)
        self.objectnum = objectnum      # Number amongst objects

        