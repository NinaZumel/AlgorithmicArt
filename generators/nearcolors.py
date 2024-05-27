'''
Inspired by https://codegolf.stackexchange.com/questions/22144/images-with-all-colors:

Create an image from a list of colors where every color is used exactly once.
The original challenge started from the list of 32768 15-bit colors to create a 256 x 128 image.

I've adapted my original solution to optionally take the list of colors from another image. 
Any duplicate colors in the list are kept; the generated image will have colors in the same distribution as the original source.

My solution is similar to [this submission](https://codegolf.stackexchange.com/a/22326) by user fejesjoco, though it's not the same.
I pick a initial pixel and color (possibly by random), then place each subsequent color such that it's nearest to the colors of its filled neighbors. 
The "neighbor distance" metric is the minimum distance from my filled neighbors.

I cheat a bit; the generated image will be the same size as its source (256 x 128 in the 15-bit color case), then I resize to the desired size using Image.resize(), 
with Image.Resampling.NEAREST to upsample while preserving the original list of colors. Using the default resampling filter (BICUBIC) produces lovely smoothed images, 
but obscures the properties of the original algorithm.

'''

from PIL import Image
import numpy as np
from typing import List, Optional
from generators.genutils import *


def _generate(colorlist: List[ColorClass], ptarray: PointArray, seed_point:int=None, width:int=None, height:int=None, rng:np.random.default_rng=None) -> Image:
    N = ptarray.converter.N

    if rng is None:
        rng = np.random.default_rng()

    # pick the initial point
    if seed_point is None:
        p0 = rng.integers(0, N, size=1)[0]
    else:
        p0 = seed_point

    # shuffle the colorlist, and take the first color as the initial color
    colorlist = list(rng.permutation(colorlist))
    c0 = colorlist.pop(0)
    ptarray.aspoint(p0).color = c0

    # re-sort the colorlist according to c0
    colorlist = sort_colorlist(colorlist, c0)

    # fill the boundary with the closest colors
    boundary_0 = ptarray.aspoint(p0).nbrs  # list of indices
    for b in boundary_0:
        ptarray.aspoint(b).color = colorlist.pop(0)

    # get the new boundary
    filled = set(boundary_0 + [p0])
    boundary_set = set()
    for f in filled:
        boundary_set.update(ptarray.aspoint(f).nbrs)
    boundary_list = list(boundary_set.difference(filled))
    boundary_set = set(boundary_list)

    while len(colorlist) > 0:
        # get the next color
        color = colorlist.pop(0)
        
        # find the best place to put this color
        mindist = np.Infinity
        best = None
        for b in boundary_list:
            d = ptarray.nbr_distance(b, color)
            if d < mindist:
                mindist = d
                best = b
        assert(best is not None)
        assert(ptarray.aspoint(best).color is None)
        ptarray.aspoint(best).color = color

        # move the point to the filled list
        filled.add(best)
        # add the new neighbors to the boundary
        boundary_set.update(ptarray.aspoint(best).nbrs)
        boundary_set = boundary_set.difference(filled)

        # Doing it this way so I traverse the boundary roughly in temporal order of insertion; a set won't preserve that.
        boundary_list = [b for b in boundary_list if b in boundary_set] + [b for b in boundary_set if b not in set(boundary_list)]

        assert(len(filled) == (N - len(colorlist)) )

    # let's make sure that we didn't miss any spots 
    blanks = [p for p in ptarray.pointlist if p.color is None]
    assert(len(blanks)==0)
    
    return ptarray.create_image(width, height)

#
# Generate an image.
# The base image is always the same size as the input image (or 256x128, if no image), then resized
# If no width, height is given, then the final image is the same size as the input image
#
def nearcolors_image(imgfile:str = None, seed_point:int=None, width:int=None, height:int=None, rng:np.random.default_rng=None) -> Image:
    """
    Generate an image by laying down colors by neighborhood similarity. The base image is the same size as the input image, 
    or 256x128 if no image is used, then resized according to (width, height).

    Parameters:
    imgfile (str): the name of an image file to get a list of colors. If None (default), uses the the list of 32768 15-bit colors.
    seed_point (int): designates the starting location (of the flattened image). 0 is the top left corner. If None (default), uses a random start position.
    width (int), height (int): size of the generated image. If None (default), uses the corresponding dimension of the base image.
    rng:(numpy.random._generator.Generator): if None (default), creates a fresh random number generator

    Returns:
    PIL.Image: the generated image
    """
    if imgfile is None:
        # initialize the colorlist, which is a list of ColorClass objects
        colorlist = []
        for r in range(0, 32):
            for g in range(0, 32):
                for b in range(0, 32):
                    color = (r * 8, g * 8, b * 8)
                    colorlist.append(ColorClass(color))

        # initialize the point array
            ptarray = PointArray(nbrhood_type=NBRHOOD.ALL)
    else:
        # get the source image
        image = Image.open(imgfile)
        N = image.size[0] * image.size[1]

        # initialize the colorlist, which is a list of ColorClass objects
        colors = list(image.getdata())
        assert(len(colors) == N)
        colorlist = [ColorClass(c) for c in colors]

        # initialize the point array
        ptarray = PointArray(image=image, nbrhood_type=NBRHOOD.ALL)

    return _generate(colorlist, ptarray, seed_point, width, height, rng)

