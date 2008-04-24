#!/usr/bin/python
"""
 * userDrawingArea.py - pyPenNotes - An area a user can draw on
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
import gobject
import sys

class UserDrawingArea(gtk.DrawingArea):
    def __init__(self):
        gtk.DrawingArea.__init__(self)
        
        self.fg_color = self.get_colormap().alloc_color("#0000FF")
        self.bg_color = self.get_colormap().alloc_color("#000000")
        self.line_width = 5
        
        self.dragging = False
        
        # Each stroke is a tuple: (fg color, width, [(x,y)])
        self.strokes = []
                
        self.add_events(gtk.gdk.BUTTON_MOTION_MASK | \
            gtk.gdk.BUTTON_PRESS_MASK | \
            gtk.gdk.BUTTON_RELEASE_MASK)
        self.connect("realize", self.realize);
        self.connect("button-press-event", self.mouse_press)
        self.connect("button-release-event", self.mouse_up)
        self.connect("motion-notify-event", self.mouse_move)
        self.connect("expose-event", lambda widget,event: self.redraw())

    def realize(self, event):
        """Called when the widget is first displayed."""
        self.gc = self.get_style().fg_gc[gtk.STATE_NORMAL]
        self.gc.set_line_attributes(self.line_width, \
                            gtk.gdk.LINE_SOLID, gtk.gdk.CAP_ROUND, \
                            gtk.gdk.CAP_ROUND)
        self.redraw()

    def set_bg_color(self, bg_color):
        """
        Set the bg_color of the area.
        
        'bg_color': Anything that can be the first argument to gtk.gdk.Colormap.alloc_color
        """
        self.bg_color = self.get_colormap().alloc_color(bg_color)
        self.redraw()
    def get_bg_color(self):
        """Get the bg_color of the area. The format is lowercase hex with four digits per color."""
        return self.bg_color.to_string()
        
    def set_fg_color(self, bg_color):
        """
        Set the fg_color of the area.
        
        'bg_color': Anything that can be the first argument to gtk.gdk.Colormap.alloc_color
        """
        self.fg_color = self.get_colormap().alloc_color(bg_color)
        self.redraw()
    def get_fg_color(self):
        """Get the fg_color of the area. The format is lowercase hex with four digits per color."""
        return self.fg_color.to_string()
        
    def clear(self):
        """Clear all strokes from the area."""
        del self.strokes[:]
        self.current_stroke_points = None
        self.redraw()
    
    def get_strokes(self):
        """Returns a list of the strokes. The stroke is a tuple of (fg_color, stroke_width, [(x,y)]), where fg_color is lowercase hex with 4 digits per color."""
        return [(fg_color.to_string(), stroke_width, points) \
                 for (fg_color, stroke_width, points) in self.strokes] # Convert the fg_color to a hex string
    
    def set_strokes(self, strokes):
        """
        Set strokes and draw them on the screen.
        'strokes': A tuple of (fg_color, stroke_width, [(x,y)]), where fg_color is lowercase hex with 4 digits per color.
        """
        self.strokes = [(self.get_colormap().alloc_color(fg_color), stroke_width, points) \
                        for (fg_color, stroke_width, points) in strokes]                    # Allocate fg_color
        self.redraw()

    def new_stroke(self, x, y):
        """Create a new stroke starting at (x, y)"""    
        self.strokes.append((self.fg_color, self.line_width, [(x,y)]))
        self.current_stroke_points = self.strokes[-1][2]
        self.update_gc()
        self.add_point_to_stroke(x, y)

    def add_point_to_stroke(self, x, y):
        """Add a point to the last stroke."""
        self.current_stroke_points.append((x,y))
        self.window.draw_lines(self.gc, self.current_stroke_points[-2:])
    
    def clear_draw_screen(self, event):
        """Overdraw the screen using background color."""
        fg_backup = self.gc.foreground
        self.gc.foreground = self.gc.background
        self.window.draw_rectangle(self.gc, True, 0, 0, -1, -1)
        self.gc.foreground = fg_backup
    
    def update_gc(self):
        """Private. Update self.gc from self.fg_color, self.bg_color and self.line_width."""
        self.gc.foreground = self.fg_color
        self.gc.background = self.bg_color
        self.gc.line_width= self.line_width

    def redraw(self):
        """Redraw screen using the notes content."""
        ## step 1 - update the gc in case we have changed the background or something like that
        self.update_gc()
        
        ## step 2 - clear screen <-- will cause a flicker!
        self.clear_draw_screen(None)

        ## step 3 - redraw all the lines
        fg_backup = self.gc.foreground
        for stroke in self.strokes:
            self.gc.foreground = stroke[0]
            self.gc.line_width = stroke[1]
            self.window.draw_lines(self.gc, stroke[2])
        self.gc.line_width = self.line_width
        self.gc.foreground = fg_backup
    def undo(self):
        if len(self.strokes) >= 1:
            self.strokes.pop()
            if len(self.strokes):
                self.current_stroke_points = self.strokes[-1][2]
            self.redraw()
            
    def mouse_move(self, widget, event):
        if(self.dragging):
            self.add_point_to_stroke(int(event.x), int(event.y))
        
    def mouse_press(self, widget, event):
        self.dragging = True
        self.new_stroke(int(event.x), int(event.y))
        
    def mouse_up(self, widget, event):
        self.dragging = False
        
if __name__ == "__main__": # Show a sample UserDrawingArea
    area = UserDrawingArea()
    
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.set_default_size(480, 640)
    window.set_title("UserDrawingArea")
    window.connect("destroy", lambda w: gtk.main_quit())
    window.add(area)
    window.show_all()
    gtk.main()
    
    print "Strokes:"
    print area.get_strokes()
