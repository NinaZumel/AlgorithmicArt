'''
Inspired by https://codegolf.stackexchange.com/questions/22144/images-with-all-colors

Create an image from a list of colors where every color is used exactly once.
The original challenge started from the list of 32768 15-bit colors to create a 256 x 128 image.

I've adapted my original solution to optionally take the list of colors from another image. 
Any duplicate colors in the list are kept; the generated image will have colors in the same distribution as the original source.

I pick a initial pixel and color (possibly by random), then sort the remaining unplaced colors by distance from the original color. 
I then do a random walk (up/down/left/right) to an uncolored neighbor, filling it with the next color. I do this until get to a dead end
(ie my current pixel has no uncolored neighbors). I then pick a new random unfilled start pixel, and a new random unused color, and start another walk.
This goes until I run out of colors (and simultaneously fill all the pixels).

I cheat a bit; the generated image will be the same size as its source (256 x 128 in the 15-bit color case), then I resize to the desired size using Image.resize()
with Image.Resampling.NEAREST to upsample while preserving the original list of colors. Using the default resampling filter (BICUBIC) produces lovely smoothed images, 
but obscures the properties of the original algorithm.

'''
from PIL import Image
import numpy as np
from typing import List, Optional
from generators.genutils import *


def _generate(colorlist: List[ColorClass], ptarray: PointArray, seed_point:int=None, width:int=None, height:int=None, rng:np.random.default_rng=None) -> Image:
    N = ptarray.converter.N
    unfilled = set([i for i in range(N)])
    filled = set()

    if rng is None:
        rng = np.random.default_rng()
    if seed_point is None:
        # pick a random start point
        p0 = rng.choice(list(unfilled))
    else:
        p0 = seed_point

    # pick a random start color, then resort the color list to that color
    c0 = rng.choice(colorlist)
    colorlist = sort_colorlist(colorlist, c0) # this should put c0 at the top
    assert(c0 == colorlist[0])

    # assign c0 to p0
    ptarray.aspoint(p0).color = colorlist.pop(0)
    filled.add(p0)
    unfilled.remove(p0)


    # pick a random neighbor from my point, and put in the next nearest color
    while len(colorlist) > 0:
        choices = set(ptarray.aspoint(p0).nbrs).difference(filled)
        if len(choices) > 0:
            # go to a random unfilled neighbor, if there is one
            pnext = rng.choice(list(choices))
            ptarray.aspoint(pnext).color = colorlist.pop(0)
            filled.add(pnext)
            unfilled.remove(pnext)
            p0 = pnext
        else:
            # pick a new random start and color
            p0 = rng.choice(list(unfilled))
            c0 = rng.choice(colorlist)
            colorlist = sort_colorlist(colorlist, c0)
            ptarray.aspoint(p0).color = colorlist.pop(0)
            filled.add(p0)
            unfilled.remove(p0)

        assert(len(unfilled) == len(colorlist))

    # let's make sure that we didn't miss any spots 
    blanks = [p for p in ptarray.pointlist if p.color is None]
    assert(len(blanks)==0)
    
    return ptarray.create_image(width, height)


def randomwalk_image(imgfile:str = None, seed_point:int=None, width:int=None, height:int=None, rng:np.random.default_rng=None) -> Image:
    """
    Generate an image by a series of random walks. The base image is the same size as the input image, or 256x128 if no image is used,
    then resized according to (width, height).

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
            ptarray = PointArray(nbrhood_type=NBRHOOD.CROSS)
    else:
        # get the source image
        image = Image.open(imgfile)
        N = image.size[0] * image.size[1]

        # initialize the colorlist, which is a list of ColorClass objects
        colors = list(image.getdata())
        assert(len(colors) == N)
        colorlist = [ColorClass(c) for c in colors]

        # initialize the point array
        ptarray = PointArray(image=image, nbrhood_type=NBRHOOD.CROSS)

    return _generate(colorlist, ptarray, seed_point, width, height, rng)