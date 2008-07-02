"""
 * 2d_slider_test.py
 *  2D slider widget - test program
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

import gtk
import slider_2d

def delete_event(widget, event, data=None):
    print("closing")
    gtk.main_quit()

def x_changed_callback(new_x_value):
    value_x_label.set_text("Value X: %s" % new_x_value)

def y_changed_callback(new_y_value):
    value_y_label.set_text("Value Y: %s" % new_y_value)


## main program ##
window = gtk.Window(gtk.WINDOW_TOPLEVEL)
window.set_title("2D Slider Test Program")
window.connect("delete_event", delete_event)
window.set_border_width(0)
window.set_default_size(450, 335)

value_x_label = gtk.Label("Value X: none")
value_y_label = gtk.Label("Value Y: none")

init_box = gtk.VBox()
init_box.set_border_width(35)

slider_2d = slider_2d.slider_2d(\
                    x_range = (0, 20), y_range = (0, 15))

slider_2d.connect('x_value_changed_event', x_changed_callback)
slider_2d.connect('y_value_changed_event', y_changed_callback)

init_box.pack_start(slider_2d, True, True, 0)
init_box.pack_start(value_x_label, False, False, 0)
init_box.pack_start(value_y_label, False, False, 0)
init_box.show_all()
window.add(init_box)
window.show_all()

gtk.main()
