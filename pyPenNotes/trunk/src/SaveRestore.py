"""
 * saveRestore.py - pyPenNotes - Save and restore the notes
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
from pyPenNotes import COLOR_LIST

class PenNote:
    def __init__(self, bg_color="#000000000000", strokes=[]):
        self.bg_color = bg_color
        self.strokes = strokes[:] # Copy to make sure we don't run into strange bugs due to mutable objects


class BaseSaveRestore:
    """Abstract class for saving and restoring notes."""
    
    def __init__(self):
        
        # Changes that are not yet saved.
        self.changes = {}
        
        # Quality loss in the compression (remove unneeded points). Measured in pixels.
        self.quality_loss = 0
        
    def revert_changes(self):
        self.changes = {}
    
    def get_note(self, index):
        """
        Abstract. Get a note by it's index.
        Returns a SaveRestore.PenNote
        """
        pass

    def in_line(self, point1, point2, point3):
        """Check if the three points are in line, making the point in the middle unneeded."""
        
        # Check if point2 is equal to or at most 'self.quality_loss' pixels different than point1
        if abs(point1[0] - point2[0]) < self.quality_loss \
           and abs(point1[1] - point2[1]) < self.quality_loss:
            return True
        
        # Todo: Detect more unneeded points by looking for straight lines etc.

    def compress_note(self, note):
        """
        Compress a note by removing unneeded points.
        
        'note': The note to compress
        """
        count = 0
        for stroke in note.strokes:
            for index, point in enumerate(stroke[2]):
                while len(stroke[2]) > (index + 2) \
                      and self.in_line(stroke[2][index], stroke[2][index+1], stroke[2][index+2]):
                    del stroke[2][index+1]
                    count += 1
        print "Deleted %i points from a note." % count
        return note
        

    def set_note(self, index, penNote):
        self.changes[index] = self.compress_note(penNote)
    
    def save(self):
        """Abstract. Save all changes."""
        pass
        
class BasicFile(BaseSaveRestore):
    """Save to a basic file. Load everything into memory on startup."""
    
    def __init__(self, file_name="~/.penNotes.strokes_data"):
        """
        Initialize and load all the data into memory.
        'file_name': The name of the file where the data is stored
        """
        BaseSaveRestore.__init__(self)
        
        self.file_name =  os.path.expanduser(file_name)
        self.pen_notes = [] # Not really necessary, as it will be defined in load() anyway, but keeping it here too so that __init__ sort of contains an overview of all data attributes
        
        self.load()
    
    def get_note(self, index):
        if self.changes.has_key(index):
            return self.changes[index]
        elif len(self.pen_notes) > index:
            return self.pen_notes[index]
        else:
            return PenNote()
       
    def load(self):
        """Load data from the data file."""
        ## throw away the old stuff :-(
        self.pen_notes = []
        
        count = 0 

        if os.path.exists(self.file_name):
            file_fd = open(self.file_name, 'r')
            try:
                for line in file_fd.read().split('\n'):
                    comma_values = line.split(",")
                    if len(comma_values) >= 2:  ## at least 1 coord
                        if len(line.split(";")[1].rstrip()) <= 0:
                            continue
                        if not len(self.pen_notes):
                            raise Exception("Bad data file: %s" % self.file_name)
                        fg_color = COLOR_LIST[int(comma_values[0])]
                        bg_color = COLOR_LIST[int(comma_values[1])]
                        thickness = int(comma_values[2].split(";")[0])
                        
                        self.pen_notes[-1].bg_color = bg_color
                        self.pen_notes[-1].strokes.append((fg_color, thickness, []))
                        
                        for coord in line.split("; ")[1].split(" "):
                            coords = coord.split(",")
                            if len(coords) <= 1:
                                continue

                            self.pen_notes[-1].strokes[-1][2].append((int(coords[0]), int(coords[1])))
                    else:
                        if len(line) >= 1:
                            count += 1
                            self.pen_notes.append(PenNote())
            finally:
                file_fd.close()
        else:
            print "No notebook file found - using an empty one."
        
        print "Loaded %i notes from %s." % (count, self.file_name)
    
    def save(self):
        """
        save data to file - format is:
        Note 001
        fg, bg, thickness; x,y x,y x,y
        fg, bg, thickness; x,y x,y x,y
        Note 002
        fg, bg, thickness; x,y x,y x,y
        """
        file_fd = open(self.file_name, 'w')
        count = 0
        
        # Move changes from self.changes to self.pen_notes
        for index, note in self.changes.iteritems():
            while len(self.pen_notes) <= index: # The user has created a new note. Create new notes until we reach index
                self.pen_notes.append(PenNote())
            self.pen_notes[index] = note
        
        
        for note in self.pen_notes:
            bg_color = note.bg_color
            count += 1
            file_fd.write("Note %4.4d\n" %count)

            for piece in note.strokes:
                fg_color = piece[0]
                thickness = piece[1]
                line = "%d, %d, %d; " %(COLOR_LIST.index(fg_color), COLOR_LIST.index(bg_color), thickness)
                if len(piece[2]) >= 1:
                    for coord in piece[2]:
                        line += "%d,%d " % coord
                file_fd.write("%s\n" %line)
        
        file_fd.close()
        
        print "Saved %i notes to %s." % (count, self.file_name)
