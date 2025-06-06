# Handles conversion between mm and scale size
# Has limited scale sizes (set using constructor)
import sys

class Scale():
    
    scales = {
        'N': 148,      # Note that some of the objects are very small with N scale
        'OO': 76.2,
        'HO': 87,
        'O': 48,
        'TT': 120,
        'G': 22.5,
        'F': 20.3,
        'Gauge 1': 32,    # Gauge 1one
        'Gauge 3': 22.6,  # Gauge 3 (full size equivelant of G)
        '16mm': 19    # 16mm scale 
        }

    mm_to_pixel_factor = 3.8
    
    # Scale can be a model railway from list "scales" or value (used for screen)
    # If not defined use default of OO - can change later
    def __init__ (self, scale='OO'):
        if (scale in self.scales):
            self.scale = scale
        else:
            # If try and choose a scale that doesn't exist then cannot continue
            # Alternative is to leave to default and try and change later
            print (f"Invalid scale - {scale} is not supported")
            sys.exit("Need valid scale")
    
    # set_scale used for outputting for SVG
    # Uses scale "names"
    # For graphics set_view_scale - allows 
    def set_scale (self, scale):
        if  (scale in self.scales.keys()):
            self.scale = scale
            return self.scale
        else:
            return None
    
    # Return list of supported scales
    def get_scales(self):
        return self.scales.keys()
    
    
    # Perform conversion from mm to scale mm
    # Normally do before convert to pixels
    def scale_convert(self, mm_value):
        return (mm_value / self.scales[self.scale])
    
    # Does the opposite of scale convert - use when you need to keep
    # exact size (eg. material thickness) - apply this then when it's
    # scaled normally then it's back to normal - some losses due to rounding
    # Still apply the mm_to_pixel separately
    def reverse_scale_convert(self, mm_value):
        return mm_value * self.scales[self.scale]
    
    # Normally use after converting to scale mm to convert to pixel size for SVG file
    # Preferable than using mm in svg due to problems with translation with some apps
    def mm_to_pixel(self, mm_value):
        return (mm_value * self.mm_to_pixel_factor)
    
    # Convert from pixels to mm
    def pixel_to_mm(self, pixel_value):
        return (pixel_value / self.mm_to_pixel_factor)
        
    
    # Plural of mm_to_pixel - convert all entries in tuple or list
    def mms_to_pixels(self, mm_values):
        return_list = []
        for value in mm_values:
            return_list.append(self.mm_to_pixel(value))
        return return_list
    
    # Convert does full conversion from mm to scale to mm
    # Can handle list of values or single value
    def convert(self, mm_values):
        # if a single value
        if (isinstance(mm_values, int) or isinstance(mm_values, float)): 
            scale_mm = self.scale_convert(mm_values)
            pixel_value = self.mm_to_pixel(scale_mm)
            return pixel_value
        # Otherwise multiple values
        return_list = []
        for mm_value in mm_values:
            scale_mm = self.scale_convert(mm_value)
            pixel_value = self.mm_to_pixel(scale_mm)
            return_list.append(pixel_value)
        return return_list
    
    
    
        