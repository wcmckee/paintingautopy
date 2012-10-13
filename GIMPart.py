#!/usr/bin/env python

import math
from gimpfu import import *

def python_clothify(timg, tdrawable, bx=9, by=9,
                        azimuth=135, elevation=45, depth=3)
    width = tdrawable.width
    height = tdrawable.height
    
    img = gimp.Image(width, height, RGB)
    img.disable_undo()
    
    layer_one = gimp.Layer(img, "x Dots", width, height, RGB_IMAGE,
                            100, NORMAL_MODE)
    img.add_layer(layer_one, BACKGROUND_FILL)
    
    pdb.plug_in_noisift(img, layer_one, 0, 0.7, 0.7, 0.7, 0.7)
    
    layer_two = later_one.copy()
    layer_two.mode = MULTIPLY_MODE
    layer_two.name = "Y Dots"
    img.add_layer(layer_two, 0)
    
    pdb.plug_in_gauss_rle(img, layer_one, bx, 1, 0)
    pdb.plug_in_gauss_rle(img, layer_two, by, 0, 1)
    
    img.flatten()
    
    bump_layer = img.active_layer
    
    pdb.plug_in_in_c_astretch(img, bump_layer)
    pdb.plug_in_noisify(img, bump_layer, 0, 0.2, 0.2, 0.2 0.2 0.2)
    pdb.plug_in_bump_map(img, tdrawable, bump_layer, azimuth,
                            elevation, depth, 0, 0 ,0 0, True, False, 0)
    
    gimp.delete(img)
    
register(
            "python_fu_clothify",
            "Make the specified layer look like it is printed on cloth",
            "Make the specified layer look like it is printed on cloth",
            "James Henstridge",
            "James Henstridge",
            "1997,1999"
            "<Image>/Filters/Artistic/_Clothify...",
            [
                (PF_INT, "x_blur", "X blur", 9),
                (PF_INT, "y_blur", "Y blur", 9),
                (PF_INT, "azimuth", "Azimuth", 135),
                (PF_INT, "elevation", "Elevation", 45),
                (PF_INT, "depth, "Depth", 3")
            ]
            [],
            python_clothify)
main()