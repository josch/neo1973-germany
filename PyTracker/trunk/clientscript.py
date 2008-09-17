from PyTrackerClient import *

test=TrackClient('edistar','refeco3','80.61.221.9')
test.StartTrack()
# I need an event to call test.StopTrack!
# How do I do that? Best would be KeyPressed("q") or something
ecore.main_loop_begin()
