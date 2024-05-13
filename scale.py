import sys


class Scale():
    
    
    scales = {
        'N': 148,
        'OO': 76.2,
        'HO': 87,
        'TT': 120,
        'G': 22.5
        }

    mm_to_pixel_factor = 3.543307
    
    # If not defined use default of OO - can change later
    def __init__ (self, scale='OO'):
        if (scale in self.scales):
            self.scale = scale
        else:
            # If try and choose a scale that doesn't exist then cannot continue
            # Alternative is to leave to default and try and change later
            print (f"Invalid scale - {scale} is not supported")
            sys.exit("Need valid scale")
    
    def set_scale (self, scale):
        if  (scale in self.scales):
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
        scale_mm = mm_value / self.scales[self.scale]
        return scale_mm
    
    # Normally use after converting to scale mm to convert to pixel size for SVG file
    # Preferable than using mm in svg due to problems with translation with some apps
    def mm_to_pixel(self, mm_value):
        pixel_value = mm_value * self.mm_to_pixel_factor
        return pixel_value
    
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
    
    
    
        