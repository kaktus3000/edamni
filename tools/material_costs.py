#!/usr/python3

import numpy
import sys
import elemfile
import configparser

def get_material_costs(infile):
	aElems, dMics, dSpeakers, dx = elemfile.scanElemFile(infile)
	
	aCrossSections = []
	aDampened = []
			
	for elem in aElems:
		if not elem.m_bGeom:
			continue
		if elem.m_fDamping > 0:
			aDampened.append(len(aCrossSections))

		aCrossSections.append(elem.m_fArea)

	#read design parameters and specific costs
	config = configparser.ConfigParser()

	config.read("material_cost.ini")
	#panel thickness relative to enclosure edge length
	d_panel_scale = float(config.get("material_costs", "d_panel_scale"))
	#specific cost of panel material per volume
	k_spec_panel = float(config.get("material_costs", "k_spec_panel"))
	#specific cost of damping material per volume
	k_spec_damper = float(config.get("material_costs", "k_spec_damper"))

	#calculate volume of horn
	vol = numpy.sum(aCrossSections) * dx 
	#calculate surface area of square horn geometry
	surface = numpy.sum(numpy.sqrt(aCrossSections) ) * dx * 4
	#calculate side length of cube enclosure
	length = numpy.power(vol, 1/3.0)
	#calculate dampened volume
	volDampened = numpy.sum(numpy.asarray(aCrossSections)[aDampened] ) * dx

	#thickness of panels
	panel = length * d_panel_scale

	#enclosure costs scale with volume (l^3)
	#area of panels in l^2 and thickness of panels in l

	k_enclosure = length * length * 6 * panel * k_spec_panel

	#costs for horn surface scale with thickness of panel (in l)
	k_surface = surface * panel * k_spec_panel

	#costs for damping material
	k_damping = volDampened * k_spec_damper
	
	dResult = {"air_volume" : vol,
				"surface_area" : surface,
				"edge_length" : length,
				"panel_thickness" : panel,
				"cost_enclosure" : k_enclosure,
				"cost_surface" : k_surface,
				"cost_damping" : k_damping,
				"cost_total" : k_enclosure + k_surface + k_damping}
				
	return dResult

if __name__ == "__main__":

	infile = sys.argv[1]
	outfile = sys.argv[2]

	dResult = get_material_costs(infile)

	f = open(outfile , "wt")

	f.write("air volume\t" + str(dResult["air_volume"]) + "\n")
	
	'''
	f.write("horn surface area\t" + str(surface) + "\n")
	f.write("length of cube enclosure\t" + str(length) + "\n")

	f.write("panel thickness\t" + str(panel) + "\n")
	f.write("cost enclosure\t" + str(k_enclosure) + "\n")
	f.write("cost horn surface\t" + str(k_surface) + "\n")
	f.write("cost damping material\t" + str(k_damping) + "\n")
	f.write("total cost\t" + str(k_enclosure + k_surface + k_damping) + "\n")

	f.close()
	'''
