strFileName = "segment.xml"

nSegments = 10
minCS = 4e-4
maxCS = 1e-2

minChamber = .04
maxChamber = .2

meanChamber = 0.5 * (minChamber + maxChamber)

minLen = .07
maxLen = .25

meanLen = 0.5 * (minLen + maxLen)

with open(strFileName, 'w') as f:
	f.write("<?xml version=\"1.0\" encoding=\"UTF-8\" ?><!DOCTYPE horn SYSTEM \"../horn.dtd\"><horn dx=\"0.02\"><tspset id=\"visaton frs 8m-8\"><Re>7.2</Re><Cms>0.0009000000000000001</Cms><Le>0.0003</Le><Rms>0.436332313</Rms><Sd>0.0029000000000000002</Sd><Mmd>0.0017099459028558936</Mmd><BL>4.0</BL></tspset>")
	
	lSections = []
	for iSection in range(nSegments):
		lSections.append("Segment" + str(iSection) )
	
	lSections = ["end_space"] + lSections + ["chamber"]
	
	f.write("<space id=\"end_space\"><neighbor1 ref=\"" + lSections[1] + "\" /><a1 min=\"" + str(minCS) + "\" max=\"" + str(maxCS) + "\" id=\"end_space_area\">0.005</a1><length>1.0</length><fraction>0.5</fraction><screen_position x=\"72\" y=\"54\" /><screen_rotation rot=\"2\" /></space>")

	f.write("<speaker id=\"Speaker\"><neighbor2 ref=\"start_space\" /><neighbor1 ref=\"chamber\" /><a1>0.01</a1><a2>0.01</a2><type>visaton frs 8m-8</type><screen_position x=\"237\" y=\"268\" /><screen_rotation rot=\"0\" /></speaker>")

	f.write("<space id=\"start_space\"><neighbor1 ref=\"Speaker\" /><a1>0.01</a1><length>1.0</length><fraction>0.5</fraction><screen_position x=\"389\" y=\"273\" /><screen_rotation rot=\"0\" /></space>")
	
	strSection = ""
	
	for iSection in range(1,len(lSections) - 1):
		strLast = lSections[iSection - 1]
		strNext = lSections[iSection + 1]
		strCurrent = lSections[iSection]
		
		f.write("<conical id=\"" + strCurrent + "\"><neighbor1 ref=\"" + strLast + "\" /><neighbor2 ref=\"" + strNext + "\" /><a1 min=\"" + str(minCS) + "\" max=\"" + str(maxCS) + "\" id=\"" + strLast + "_area\">0.005</a1><a2 min=\"" + str(minCS) + "\" max=\"" + str(maxCS) + "\" id=\"" + strCurrent + "_area\">0.005</a2><length min=\"" + str(minLen) + "\" max=\"" + str(maxLen) + "\" id=\"len\">" + str(meanLen) + "</length><damping_constant>0.0</damping_constant><screen_position x=\"389\" y=\"170\" /><screen_rotation rot=\"0\" /></conical>")
	
	f.write("<conical id=\"chamber\"><neighbor1 ref=\"Speaker\" /><neighbor2 ref=\"" + lSections[-2] + "\" /><a1>0.01</a1><a2>0.01</a2><length min=\"" + str(minChamber) + "\" max=\"" +  str(maxChamber) + "\" id=\"box_decaliters\">0.1</length><damping_constant>1000.0</damping_constant><screen_position x=\"80\" y=\"273\" /><screen_rotation rot=\"2\" /></conical>")
	
	f.write("</horn>")

