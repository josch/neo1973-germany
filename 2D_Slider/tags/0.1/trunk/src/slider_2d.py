"""
 * 2d_slider.py
 *  widget to allow for 2D selection of values
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

import os
import gtk

IMAGE_DIRECTORY = os.path.join(os.path.realpath(os.path.curdir), "./")
POINT_IMAGE = os.path.join(IMAGE_DIRECTORY, "point.png")
POINT_INV_IMAGE = os.path.join(IMAGE_DIRECTORY, "point_inv.png")
IMAGE_SIZE_X = 10
IMAGE_SIZE_Y = 10


class slider_2d(gtk.HBox):
    """
    Widget to allow for two dimensional selection of values
    """
    
    def __init__(self, x_range = (0, 10), y_range = (0, 10), 
                                bg_color = "#222222", fg_color = "#555566"):
        gtk.HBox.__init__(self, False, 0)
    
        self.x_range = x_range
        self.y_range = y_range
        self.x_resolution = x_range[1] - x_range[0]
        self.y_resolution = y_range[1] - y_range[0]
        self.bg_color = bg_color
        self.fg_color = fg_color

        self.x_value = int(x_range[1] - x_range[0] / 2)
        self.y_value = int(x_range[1] - x_range[0] / 2)
        self.mouse_x_position = -1
        self.mouse_y_position = -1
        self.clicked = False

        self.area = gtk.DrawingArea()
        self.area.set_size_request(400, 300)
        style = self.area.get_style()
        self.gc = style.fg_gc[gtk.STATE_NORMAL]
        self.area.set_events(gtk.gdk.POINTER_MOTION_MASK |
                             gtk.gdk.POINTER_MOTION_HINT_MASK )
        self.area.add_events(gtk.gdk.BUTTON_MOTION_MASK | \
            gtk.gdk.BUTTON_PRESS_MASK | \
            gtk.gdk.BUTTON_RELEASE_MASK)
        self.area.connect("expose-event", self.area_expose_cb)
        self.area.connect("button-press-event", self.area_click_cb)
        self.area.connect("button-release-event", self.area_unclick_cb)
        self.area.connect("motion-notify-event", self.area_mousemove_cb)

        self.x_value_changed_callback = 0
        self.y_value_changed_callback = 0

        # define Horizontal and Vertical Rulers
        self.hruler = gtk.HRuler()
        self.vruler = gtk.VRuler()
        self.hruler.set_range(x_range[0], x_range[1], x_range[0], x_range[1])
        self.vruler.set_range(y_range[0], y_range[1], y_range[0], y_range[1])

        def motion_notify(ruler, event):
            return ruler.emit("motion_notify_event", event)

        self.area.connect_object("motion_notify_event", motion_notify,
                                                                    self.hruler)
        self.area.connect_object("motion_notify_event", motion_notify,
                                                                    self.vruler)

        def size_allocate_cb(wid, allocation):
            x, y, width, height = allocation
            lower, upper, position, max_size = self.hruler.get_range()
            self.hruler.set_range(lower, self.x_resolution, position, max_size)
            lower, upper, position, max_size = self.vruler.get_range()
            self.vruler.set_range(lower, self.y_resolution, position, max_size)
            self.width = width
            self.height = height
        self.area.connect('size-allocate', size_allocate_cb)


        self.table = gtk.Table(2,2)
        self.table.attach(self.hruler, 1, 2, 0, 1, yoptions=0)
        self.table.attach(self.vruler, 0, 1, 1, 2, xoptions=0)
        self.table.attach(self.area, 1, 2, 1, 2)

        self.add(self.table)


    def connect(self, event_name, callback):
        if event_name == "x_value_changed_event":
            self.x_value_changed_callback = callback
        elif event_name == "y_value_changed_event":
            self.y_value_changed_callback = callback
        else:
            super(slider_2d, self).connect(event_name, callback)
        

    ############################################################################
    ## callbacks to draw 2D Slider #############################################
    ############################################################################
    def area_expose_cb(self, area, event):
        self.redraw()

    def area_click_cb(self, area, event):
        self.clicked = True
        self.put_value_point(area)

    def area_unclick_cb(self, area, event):
        self.clicked = False
        self.put_value_point(area)

    def area_mousemove_cb(self, area, event):
        pos = area.get_pointer()

        x_max = self.width * 1.0 -1
        y_max = self.height * 1.0 -1
        x_spacing = x_max / self.x_resolution
        y_spacing = y_max / self.y_resolution
        
        # get position of point in grid
        x = int((pos[0] + x_spacing/2) / x_spacing)
        y = int((pos[1] + y_spacing/2) / y_spacing)

        if self.mouse_x_position != x or self.mouse_y_position != y:
            self.redraw_area(self.mouse_x_position, self.mouse_y_position)
            self.mouse_x_position = x
            self.mouse_y_position = y
            self.show_inv_point(x, y)

        if self.clicked:
            self.put_value_point(area)

    
    def put_value_point(self, area):
        """
        actually setting a new value
        """
        pos = area.get_pointer()

        x_max = self.width * 1.0 -1
        y_max = self.height * 1.0 -1
        x_spacing = x_max / self.x_resolution
        y_spacing = y_max / self.y_resolution
        
        # get position of point in grid
        x = int((pos[0] + x_spacing/2) / x_spacing)
        y = int((pos[1] + y_spacing/2) / y_spacing)
        
        if (self.x_value != x or self.y_value != y) \
                            and x in range(self.x_range[0], self.x_range[1]+1)\
                            and y in range(self.y_range[0], self.y_range[1]+1):
            backup_x = self.x_value
            backup_y = self.y_value
            self.x_value = x
            self.y_value = y
            self.redraw_area(backup_x, backup_y)
            self.show_point(self.x_value, self.y_value)

            # here we call the callbacks!
            if backup_x != self.x_value:
                self.x_value_changed_callback(self.x_value)
            if backup_y != self.y_value:
                self.y_value_changed_callback(self.y_value)


    ############################################################################
    ## actually writing to our area ############################################
    ############################################################################

    def redraw(self):
        """ 
        writing all elements to drawing area 
        (clears screen, draws grid, draws value)
        """

        # get gc
        style = self.area.get_style()
        self.gc = style.fg_gc[gtk.STATE_NORMAL]
    
        # clear screen
        if self.gc:
            fg_backup = self.gc.foreground
            self.gc.foreground = self.area.window.get_colormap()\
                                            .alloc_color(self.bg_color)
            # 1) clear screen
            self.area.window.draw_rectangle(self.gc, True, 0, 0, -1, -1)
            self.gc.foreground = fg_backup

            backup_fb = self.gc.foreground
            try:
                self.gc.foreground = self.area.window.get_colormap()\
                                                .alloc_color(self.fg_color)
                self.gc.set_line_attributes(1, \
                        gtk.gdk.LINE_SOLID, gtk.gdk.CAP_ROUND, \
                        gtk.gdk.CAP_ROUND)

                # 2) draw grid
                x_max = self.width * 1.0 -1
                y_max = self.height * 1.0 -1
                x_spacing = x_max / self.x_resolution
                y_spacing = y_max / self.y_resolution
                for i in range(self.x_resolution+2):
                    self.area.window.draw_line(self.gc, int(x_spacing * i), 0, int(x_spacing * i), int(y_max))

                for i in range(self.y_resolution+2):
                    self.area.window.draw_line(self.gc, 0, int(y_spacing * i), int(x_max), int(y_spacing * i))
            finally:
                self.gc.foreground = backup_fb
            self.show_point(self.x_value, self.y_value)

    def draw_pixmap(self, x, y, img):
        """ 
        loads and draws image to our area 
        """

        pixmap, mask = gtk.gdk.pixmap_create_from_xpm(self.area.window, \
            self.area.window.get_colormap().alloc_color(self.bg_color), img)

        self.area.window.draw_drawable(self.gc, pixmap, 0, 0, \
                                                    int(x-5), int(y-5), -1, -1)

    def show_point(self, x_value, y_value):
        """ 
        shows the value-marker at a specific place
        """
        x_max = self.width * 1.0 -1
        y_max = self.height * 1.0 -1
        x_spacing = x_max / self.x_resolution
        y_spacing = y_max / self.y_resolution

        self.draw_pixmap(x_spacing * x_value, y_spacing * y_value, POINT_IMAGE)

    def show_inv_point(self, x_value, y_value):
        """ 
        shows the inverted value-marker (mouse indicator) at a specific place
        """
        x_max = self.width * 1.0 -1
        y_max = self.height * 1.0 -1
        x_spacing = x_max / self.x_resolution
        y_spacing = y_max / self.y_resolution

        self.draw_pixmap(x_spacing * int(x_value), y_spacing * int(y_value),\
                                                                POINT_INV_IMAGE)

    def redraw_area(self, x_value, y_value):
        """ 
        redraws the area of a value marker, without clearing out the whole 
        screen - to prevent flickering
        """

        x_max = self.width * 1.0 -1
        y_max = self.height * 1.0 -1
        x_spacing = x_max / self.x_resolution
        y_spacing = y_max / self.y_resolution

        start_x = int((x_spacing * x_value) - (IMAGE_SIZE_X / 2))
        start_y = int((y_spacing * y_value) - (IMAGE_SIZE_Y / 2))

        fg_backup = self.gc.foreground
        self.gc.foreground = self.area.window.get_colormap()\
                                                    .alloc_color(self.bg_color)
        self.area.window.draw_rectangle(self.gc, True, \
                                start_x, start_y, IMAGE_SIZE_X, IMAGE_SIZE_Y)
        self.gc.foreground = fg_backup

        # easyest way for now: redraw all lines
        backup_fb = self.gc.foreground
        try:
            self.gc.foreground = self.area.window.get_colormap()\
                                            .alloc_color(self.fg_color)
            self.gc.set_line_attributes(1, \
                    gtk.gdk.LINE_SOLID, gtk.gdk.CAP_ROUND, \
                    gtk.gdk.CAP_ROUND)

            # 2) draw grid
            x_max = self.width * 1.0 -1
            y_max = self.height * 1.0 -1
            x_spacing = x_max / self.x_resolution
            y_spacing = y_max / self.y_resolution
            for i in range(self.x_resolution+2):
                self.area.window.draw_line(self.gc, int(x_spacing * i), 0, int(x_spacing * i), int(y_max))
            for i in range(self.y_resolution+2):
                self.area.window.draw_line(self.gc, 0, int(y_spacing * i), int(x_max), int(y_spacing * i))
        finally:
            self.gc.foreground = backup_fb

        self.show_point(self.x_value, self.y_value)
