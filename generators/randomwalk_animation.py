'''
Another random walk, but this time I'm letting the "bug" cross its own path. 
So I walk until the colors run out (by default), but don't fill the whole canvas.
'''

from PIL import Image
from numpy.random import default_rng
from IPython.display import display

from generators.genutils import *



def randomwalk(colorlist: List[ColorClass], 
               gifname:str, 
               *, 
               shuffle_colors=True,
               size:int=128, 
               scale:int=1, 
               rng:np.random._generator.Generator=None, 
               maxiters=None) ->  Image:
    
    """
    Generate a square image as by a bug on a random walk, using colors from a colorlist as the bug's "footprints." The bug can cross its own path.
    Walks until <maxiters> or all the colors in the list are used up. Generates an animated gif as a side effect, and returns the final image.

    Parameters:
    colorlist (List[generators.genutils.ColorClass]): the list of colors to use.
    gifname (str): the name of the animated gif file.
    shuffle_colors (boolean): If True (default), picks a random color to start, then re-sorts the colorlist by distance from the starting color. Otherwise, walks the list as given.
    size (int): the length of one side of the square that the bug walks, in pixels. Default is 128.
    scale (int): how much to scale up the final image (so scale=2 with the default size produces a 256x256 image). Default is 1.
    rng:(numpy.random._generator.Generator): if None (default), creates a fresh random number generator.
    maxiters (int): how many steps the bug takes. If None (default), use len(colorlist).

    Returns:
    PIL.Image: the generated image. The animated gif is produced as a side effect.
    """

    if rng is None:
        rng = default_rng()
        
    ptarray = PointArray(nbrhood_type=NBRHOOD.CROSS, image=Image.new("RGB", (size, size)))
    p0 = rng.integers(0, ptarray.converter.N)

    if shuffle_colors:
        # pick a random start color, then re-sort the color list to that color
        c0 = rng.choice(colorlist)
        colorlist = sort_colorlist(colorlist, c0) # this should put c0 at the top
    else:
        c0 = colorlist[0]

    if maxiters is None:
        maxiters = len(colorlist) # run through all the colors
    iters = 0
    frames = []
    imagesize = scale * size
    while (iters < maxiters) & (len(colorlist) > 0) :
        ptarray.aspoint(p0).color = colorlist.pop(0)
        if iters % 100 == 0:
            frames.append(ptarray.create_image(imagesize, imagesize))
        p0 = rng.choice(ptarray.aspoint(p0).nbrs)
        iters += 1

    # final frame
    frames.append(ptarray.create_image(imagesize, imagesize))
    frames[0].save(gifname, save_all=True, append_images=frames[1:], duration=100, loop=0)
    return frames[-1]