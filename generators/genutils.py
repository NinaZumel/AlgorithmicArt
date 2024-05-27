from PIL import Image
import numpy as np
from typing import List, Optional
from enum import Enum


#
# utilities for going back and forth between a linear array of points and a WIDTH x HEIGHT image.
# WIDTH and HEIGHT are taken from the source image, or 256x128 if no source image is given.
# 

class ShapeConverter:
    def __init__(self, image:Optional[Image] = None):
        # 15-bit colors case
        if image is None:
            self.WIDTH = 256
            self.HEIGHT = 128
            self.N = self.WIDTH*self.HEIGHT
        # colormap from source image case    
        else:
            self.WIDTH = image.size[0]
            self.HEIGHT = image.size[1]
            self.N = self.WIDTH*self.HEIGHT


    # convert an index [0:N) to coords (col, row)
    def index_to_coords(self, ptindex): 
        if (ptindex < 0) | (ptindex >= self.N):
            raise Exception("index out of range")
        row = np.floor(ptindex/self.WIDTH)
        col = ptindex - row * self.WIDTH
        return (int(col), int(row))  


    # convert coords (col, row) to index [0:N)
    def coords_to_index(self, coords):
        col = coords[0]
        row = coords[1]

        if (col < 0) | (col >= self.WIDTH):
            raise Exception("column coordinate out of range")
        if (row < 0) | (row >= self.HEIGHT):
            raise Exception("row coordinate out of range")

        return int((row * self.WIDTH) + col)


#
# Colors
#

class ColorClass:
    def __init__(self, rgb: tuple):
        self.rgb = rgb
        self.rgbvec = np.array(self.rgb)

    def get_distance(self, color):
        delta = self.rgbvec - color.rgbvec
        return np.sqrt(np.sum(delta*delta))
    


# sort a colorlist in ascending distance from refcolor
def sort_colorlist(colorlist: List[ColorClass], refcolor: ColorClass) -> List[ColorClass]:
    distancelist = [c.get_distance(refcolor) for c in colorlist]
    # sort colorlist based on distance
    indices = np.argsort(distancelist)
    return [colorlist[i] for i in indices]

    

#
# Points
#

class NBRHOOD(Enum):
    ALL = 1          # up/down/left/right/diagonals
    CROSS = 2        # up/down/left/right only


class Point:
    def __init__(self, index:int, converter: ShapeConverter, nbrhood_type:NBRHOOD):
        self.index = index
        self.converter = converter
        self.coords = converter.index_to_coords(index)  # tuple
        self.nbrs = self.get_nbrs(nbrhood_type)   # list of indices (not Points)
        self.color = None   # ColorClass


    def get_color(self):
        if self.color is None:
            return (0, 0, 0)
        return self.color.rgb
    

    # find my neighbors, represented as indices (not points)
    def get_nbrs(self, nbrhood_type:NBRHOOD = NBRHOOD.ALL) -> List[int] :
        x, y = self.coords
        n = 1
        xrange = range(max(x-n, 0), min(x+n+1, self.converter.WIDTH))
        yrange = range(max(y-n, 0), min(y+n+1, self.converter.HEIGHT))

        nbrs = []

        if nbrhood_type == NBRHOOD.ALL:
            for xi in xrange:
                for yi in yrange:
                    pix = self.converter.coords_to_index((xi, yi))
                    if pix != self.index:
                        nbrs.append(pix)
            return nbrs
        
        if nbrhood_type == NBRHOOD.CROSS:
            # left and right nbrs
            for xi in xrange:
                pix = self.converter.coords_to_index((xi, y))
                if pix != self.index:
                    nbrs.append(pix)
            # up and down nbrs
            for yi in yrange:
                pix = self.converter.coords_to_index((x, yi))
                if pix != self.index:
                    nbrs.append(pix)
                    
            return nbrs
        
        raise Exception("Unrecognized neighborhood type.")
    


#
# An array of Points, the same size as the input image
# Assume for now that the image mode is RGB
#

class PointArray:

    # named arguments required
    def __init__(self, *, nbrhood_type: NBRHOOD, image:Optional[Image] = None):
        if image is None:
            self.converter = ShapeConverter()
            self.pointlist = [None] * self.converter.N
            for i in range(self.converter.N):
                self.pointlist[i] = Point(i, self.converter, nbrhood_type)
        else:
            self.converter = ShapeConverter(image)
            self.pointlist = [None] * self.converter.N
            for i in range(self.converter.N):
                self.pointlist[i] = Point(i, self.converter, nbrhood_type)


    def aspoint(self, index):
        return self.pointlist[index]


    # calculate the nbr_distance of <o> from its neighbors, if <o>.color == <color>
    # the nbr_distance is the minimum color distance from the filled neighbors
    def nbr_distance(self, o:int, color:ColorClass):
        # get all the neighboring colors
        nbrcolors = [self.aspoint(n).color for n in self.aspoint(o).nbrs if self.aspoint(n).color is not None]
        distances = [nc.get_distance(color) for nc in nbrcolors]
        return min(distances)
    

    # create an image from this PointArray
    def create_image(self, width=None, height=None) -> Image:
        image = Image.new("RGB", (self.converter.WIDTH, self.converter.HEIGHT))
        pixels = [p.get_color() for p in self.pointlist]
        image.putdata(pixels)
        if width==None:
            width=self.converter.WIDTH
        if height==None:
            height=self.converter.HEIGHT

        return image.resize((width, height), resample=Image.Resampling.NEAREST)
    

