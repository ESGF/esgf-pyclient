from .consts import OPERATOR_NEQ

class GeospatialConstraint(object):
    """
    Class to encapsulate all geospatial constraints in the ESGF Search API
    """

    def __init__(self, lat=None, lon=None, bbox=None, location=None,
                 radius=None, polygon=None):
        self.lat, self.lon = lat, lon
        self.bbox = bbox
        self.location = location
        self.radius, self.polygon = radius, polygon

#-----------------------------------------------------------------------------
# Convenience functions

#!TODO: document constraint operators
        
def any_of(values):
    """
    Constrains to any of the specified values.
    This is a synonym for list(values).
    
    """
    return list(values)

def not_equals(value):
    return (OPERATOR_NEQ, value)
