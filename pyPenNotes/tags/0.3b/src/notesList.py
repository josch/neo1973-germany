"""
 * notesList.py - pyPenNotes - sort notes by correlation
 *
 * (C) 2007 by Kristian Mueller <kristian-m@kristian-m.de>
 * All Rights Reserved
 *
 * some idea from Toby Segaran's Collective Intelligence (O'Reilly 2007)
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

# get list of counted values
# corr_types can be:
# number - number of lines
# sub_number - number of lines in strokes
def count_values(notes, corr_type):
    corr_list = []

    # use number of strokes
    if corr_type == "number":
        for note in notes:
            corr_list.append(len(note.image_list))

    # use number of strokes
    if corr_type == "sub_number":
        for note in notes:
            count = 0
            for i in note.image_list:
                count += (len(i[2]))
            corr_list.append(count)

    # use line lenght
    if corr_type == "len":
        # get list of strokes by distance from start to end
        for note in notes:
            count = 0
            #for stroke in note.image_list:
            #    count += abs(stroke)
            corr_list.append(count)

    max_value = max(corr_list)
    min_value = min(corr_list)

#    print "==================================================================="
    count = 1
    for i in corr_list:
        #print "%s Elements: %s - Value %s" %(
        #                count, i, (min_value - i * (1.0 / max_value)))
        count += 1
        i = (min_value - i * (1.0 / max_value))

    return corr_list


# get Pearson correlation coefficiant for note1 and note2
def pearson_correlation(notes, note1, note2, corr_type1, corr_type2):
    vals1 = count_values(notes, corr_type1)
    vals2 = count_values(notes, corr_type2)
    
    # print "Val1:1 = %s" % vals1[note1]
    # print "Val1:2 = %s" % vals1[note2]
    # print "Val2:1 = %s" % vals2[note1]
    # print "Val2:2 = %s" % vals2[note2]
    
    # print "Distance    = %s and %s" %(abs(vals1[note1] - vals1[note2]), abs(vals2[note1] - vals2[note2]))
    print "%s" %(
        abs (abs(vals1[note1] - vals2[note1]) - abs(vals1[note2] - vals2[note2]))),

#    print "2D Distance %s<-->%s = %s" %(
#        note1, note2,
#        abs (abs(vals1[note1] - vals2[note1]) - abs(vals1[note2] - vals2[note2])))

    