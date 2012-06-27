
from .consts import ALL_OF

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

def all_of(*facet_values):
    return ([ALL_OF] + facet_values)

