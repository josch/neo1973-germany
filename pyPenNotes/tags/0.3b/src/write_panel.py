"""
 * write_panel.py - Project LDA - Pen_interface
 *
 * (C) 2008 by Kristian Mueller <kristian-m@kristian-m.de>
 * All Rights Reserved
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

COLOR_LIST = ["#0000FF", "#FF0000", "#00FF00", "#FFFF00", "#FFFFFF", "#000000"]
DEFAULT_BG = 5 ## Black
DEFAULT_FG = 0 ## Blue
DEFAULT_SIZE = 4 ## Diameter 4 Pixel



## A note is defined by its strokes a background and the line thickness.
## Strokes of the same color and thickness are combined in a strokes_list.
## The order of strokes will stay the same.
class PenNote:
    def __init__(self):
        self.bg_color = DEFAULT_BG
        self.last_fg_color = 0
        self.last_line_thickness = DEFAULT_SIZE
        self.last_stroke = (0, 0)
        self.strokes_list = []   # current list of strokes from 
                                 # the same color or thickness
                                 # strokes are tuples of src and dest
        self.image_list = []     # list of (color, thickness, strokes_list)
        self.image_list.append((self.last_fg_color, self.last_line_thickness,
                                                            self.strokes_list))

    def add_stroke(self, src, dest, color, line_thickness):
        if (color != self.last_fg_color) or \
                (self.last_line_thickness != line_thickness) \
                or self.last_stroke != src:
            self.strokes_list = []
            self.strokes_list.append((src[0], src[1]))
            self.image_list.append((color, line_thickness, self.strokes_list))
            self.last_fg_color = color
            self.last_line_thickness = line_thickness

        self.strokes_list.append((dest[0], dest[1]))
        self.last_stroke = dest

    def append_point_to_stroke(self, coord):
        self.strokes_list.append(coord)

    def append_new_point(self, coord, color, thickness):
        self.strokes_list = []
        self.strokes_list.append(coord)
        self.image_list.append((color, thickness, self.strokes_list))
        self.last_fg_color = color
        self.last_line_thickness = thickness

    def clear(self):
        self.__init__()



