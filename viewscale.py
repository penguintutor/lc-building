# Handles conversion between mm and view level 
# Based on scale, but applied to screen and fixed size
# For zoom in / zoom out then use QGraphicsView scale

class ViewScale():
    
    mm_to_pixel_factor = 3.8
    
    # Zoom factor is number representing how much to scale by
    def __init__ (self, scale_factor=50):
        self.scale_factor = scale_factor

            
    # Perform conversion from mm to scale mm
    # Normally do before convert to pixels
    def scale_convert(self, mm_value):
        scale_mm = mm_value / self.scale_factor
        return scale_mm
    
    # Does the opposite of scale convert - use when you need to keep
    # exact size (eg. material thickness) - apply this then when it's
    # scaled normally then it's back to normal - some losses due to rounding
    # Still apply the mm_to_pixel separately
    def reverse_scale_convert(self, mm_value):
        return mm_value * self.scale_factor
    
    # Normally use after converting to scale mm to convert to pixel size for SVG file
    # Preferable than using mm in svg due to problems with translation with some apps
    def mm_to_pixel(self, mm_value):
        pixel_value = mm_value * self.mm_to_pixel_factor
        return pixel_value
    
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