#!/usr/python3

#track chains of elements in the input file and draw a pretty image

import numpy
import sys

infile = sys.argv[1]
outfile = sys.argv[2]

f = open(infile, 'r')

aLines = f.readlines()

f.close()

g_dx = 0

aCrossSections = []
aDampened = []

for line in aLines:
	if line[0] == '+':
		substrings = line.split(" ")
		aCrossSections.append(float(substrings[2]) )
		
	if line[0] == 'd':
		aDampened.append(len(aCrossSections) - 1)
	
	if line[0:2] == "dx":
		g_dx = float(line[2:])



#read design parameters and specific costs

#panel thickness relative to enclosure edge length
d_panel_scale = 0.03
#specific cost of panel material per volume
k_spec_panel = 900
#specific cost of dampening material per volume
k_spec_damper = 1200
		
f = open(outfile , "wt")

#calculate volume of horn
vol = numpy.sum(aCrossSections) * g_dx 
#calculate surface area of square horn geometry
surface = numpy.sum(numpy.sqrt(aCrossSections) ) * g_dx * 4
#calculate side length of cube enclosure
length = numpy.power(vol, 1/3.0)
#calculate dampened volume
volDampened = numpy.sum(numpy.asarray(aCrossSections)[aDampened] ) * g_dx

f.write("air volume\t" + str(vol) + "\n")
f.write("horn surface area\t" + str(surface) + "\n")
f.write("length of cube enclosure\t" + str(length) + "\n")

#thickness of panels
panel = length * d_panel_scale

#enclosure costs scale with volume (l^3)
#area of panels in l^2 and thickness of panels in l

k_enclosure = length * length * 6 * panel * k_spec_panel

#costs for horn surface scale with thickness of panel (in l)
k_surface = surface * panel * k_spec_panel

#costs for damping material
k_damping = volDampened * k_spec_damper

f.write("panel thickness\t" + str(panel) + "\n")
f.write("cost enclosure\t" + str(k_enclosure) + "\n")
f.write("cost horn surface\t" + str(k_surface) + "\n")
f.write("cost damping material\t" + str(k_damping) + "\n")
f.write("total cost\t" + str(k_enclosure + k_surface + k_damping) + "\n")

f.close()

