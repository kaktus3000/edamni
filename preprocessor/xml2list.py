'''
parses XML file describing horn geometry
generates element set for simulation

output file format:

//volume element
e <#ID>			#element ID
- <#REF> <AREA>		#volume id of "negative" side adjacent elements and common cross-section
+ <#REF> <AREA>		#same for "positive" side
d <#VALUE>		#velocity damping

//speaker
s			#speaker with left and right adjacent elements, definition file
- <#REF> <AREA>		#volume id of left adjacent elements and common cross-section
+ <#REF> <AREA>		#same for right

m <#ID> <#REF>		#virtual microphone ID and reference to measured element
dx <#VALUE>		#element width

'''

import xml.etree.ElementTree as ET
import math
import sys

infile = sys.argv[1]
outfile = sys.argv[2]

#function to check whether adjacent sections have non-matching cross-sections
def check_cross_sections(hornSections):
	neighborDict = dict()
	
	for sectionID in hornSections.keys():
		(sectionType, sectionDict) = hornSections[sectionID]
#		print("checking section", sectionID, "(" + sectionType + ")")
		#check neighbors
		for propertyName in sectionDict.keys():
			propValue = sectionDict[propertyName];
#			print("checking property", propertyName)
			#see whether we have a connection to that branch
			if propertyName.find("neighbor") >=0:
				portID = propertyName.replace("neighbor", "")
				neighborID = propValue
#				print("found link to neighbor", neighborID, ", connected to port", portID)
				#now locate the link back to this section on the neighbor to get its port
				
				(neighborSectionType, neighborSectionDict) = hornSections[neighborID];
				for neighborPropertyName in neighborSectionDict.keys():
					neighborPropValue = neighborSectionDict[neighborPropertyName];
#					print("checking neighbor property", neighborPropertyName)
					#see whether we have a connection to that branch
					if neighborPropertyName.find("neighbor") >=0:
						neighborPortID = neighborPropertyName.replace("neighbor", "")
						if neighborPropValue == sectionID:
							connection_tuple = (neighborID, int(portID), int(neighborPortID))
							if sectionID in neighborDict:
								neighborDict[sectionID].append( connection_tuple )
							else:
								neighborDict[sectionID] = [connection_tuple]
							
#							print("identified link:", sectionID, "(port", portID + ")", "->", neighborID, "(port", neighborPortID + ")", ".")
							
							key1 = "A" + portID
							key2 = "A" + neighborPortID
							if (key1 in sectionDict) and (key2 in neighborSectionDict):
								crossSect1 = sectionDict[key1]
								crossSect2 = neighborSectionDict[key2]
								if crossSect1 != crossSect2:
									print("cross-sections do not match!")
#								else:
#									print("cross-sections match!")
							else:
								print("did not find", key1, "in", sectionID, "or", key2, "in", neighborID)
	#unravel neighbor dictionary
	
	return neighborDict
def conical_section(dx, params):
	#params should all be float
	A1 = params["A1"]
	A2 = params["A2"]
	
	r1 = math.sqrt(A1)
	r2 = math.sqrt(A2)
	
	length = params["length"]
	damping = params["damping_constant"]
	
	nElems = int((length / dx) + 1);
	
	outList = []
	
	lastA = A1
	positiveGradient = A2 > A1
	
	for iElem in range(nElems):
		relX=(iElem+1)/nElems
		rx=((relX)*(r2-r1) + r1);
		Ax=rx*rx

		if (Ax > A2) and positiveGradient:
			Ax = A2
		if (Ax < A2) and (not positiveGradient):
			Ax = A1

#		print(rx*rx, Ax, positiveGradient, A1, A2)

		outList.append((lastA, Ax, damping))
		
		lastA = Ax
	
	return outList

def expo_section(dx, params):
	#params should all be float
	A1 = params["A1"]
	A2 = params["A2"]
	length = params["length"]
	damping = params["damping_constant"]
	
	nElems = int((length / dx) + 1);
	
	x1 = math.log(A1)
	x2 = math.log(A2)
	
	xLen = x2-x1;
	
	lastA = A1
	positiveGradient = A2 > A1
	
#	print("b ** x2 =", math.pow(base, x2), "A2 =", A2)
	
	outList = [] 
	
	for iElem in range(nElems):
		relX=((iElem+1)/nElems) * xLen
		
		Ax=math.exp(relX + x1);
		
		if (Ax > A2) and positiveGradient:
			Ax = A2
		if (Ax < A1) and (not positiveGradient):
			Ax = A1
		
		outList.append((lastA, Ax, damping))
		
		lastA = Ax
	
	return outList

def wall_section(dx, params):
	#params should all be float
	A2 = params["A2"]
	
	length = params["damping_thickness"]
	damping = params["damping_constant"]
	
	nElems = int((length / dx) + 1);
	print("creating", nElems, "wall elements")
	
	outList = [(A2, A2, damping)]*nElems
	
	return outList

def mouth_section(dx, params):
	#params should all be float
	A1 = params["A1"]
	
	free_length = params["free_length"]
	space = params["space"]
	
	nFreeElems = int((free_length / dx) + 1);
	print("creating", nFreeElems, "free wall elements")
	
	lastA = A1
	outList = []
	
	for iElem in range(nFreeElems):
		r = iElem * dx
		surf = space * 4.0 * math.pi * r * r
		rim = space * 2.0 * math.pi * math.pi * math.sqrt(A1/math.pi) * r
		Ax = A1 + surf + rim
		
		outList.append((lastA, Ax, 0))
		lastA = Ax
	
	return outList

#dict of functions, working this way:
#[(area1, area2, damping)] = geometryHandlers["geom"](dx, params)
#where dx is the width of the elements
#return value is a list of the elements, sorted from neighbor1 to neighbor2
geometryHandlers = dict()
geometryHandlers["conical"] = conical_section
geometryHandlers["expo"] = expo_section
geometryHandlers["wall"] = wall_section
geometryHandlers["mouth"] = mouth_section


tree = ET.parse(infile)
horn = tree.getroot()

if horn.tag != "horn":
	print("malformed xml: root elem has to be horn!")
	exit();
	
dx = float(horn.attrib["dx"])
#print("dx =", dx)

hornDict = dict()
#print("dumping xml input")

for section in horn:
	if not "id" in section.attrib:
		print("malformed xml: elem", section.tag, "has no 'id' attribute!")
#	print(section.tag, "(" + section.attrib["id"] + ")")
	
	this_section_dict = dict()
	
	for elem in section:
		elemText = elem.text
		if elem.tag.find("neighbor") >=0:
			elemText = elem.attrib["ref"];
		else:
			try:
				elemText = float(elem.text);
			except:
				pass
#		print(elem.tag, "=", elemText)
		this_section_dict[elem.tag] = elemText
		
	hornDict[section.attrib["id"]] = (section.tag, this_section_dict)

#check whether the cross-sections given are discontinuous
neighborDict = check_cross_sections(hornDict)

print("dumping neighbors dictionary")

print(neighborDict)

hElemFile=open(outfile, "wt")
hElemFile.write("dx " + str(dx) + "\n")

#neighbors := [(id, area)]
def writeElem(elID, negNeighbors, posNeighbors, velDamp):
	hElemFile.write("e " + elID)
	hElemFile.write("\n")
	for (negNeighbor, area) in negNeighbors:
		hElemFile.write("- " + negNeighbor + " " + str(area))
		hElemFile.write("\n")
	for (posNeighbor, area) in posNeighbors:
		hElemFile.write("+ " + posNeighbor + " " + str(area))
		hElemFile.write("\n")
		
	if velDamp != 0:
		hElemFile.write("d " + str(velDamp))
		hElemFile.write("\n")

wallID = 0
currElID = 1

begEndDict = dict()
elementNumber = 1
for sectionID in hornDict.keys():
	(sectionType, sectionDict) = hornDict.get(sectionID);
	if sectionType in geometryHandlers:
		begEndDict[sectionID] = [currElID, currElID + 1]
		currElID += 2
	else:
		continue
#		begEndDict[sectionID] = [currElID]
#		currElID += 1

print("dumping beginning and end cell dictionary")
print(begEndDict)

begEndConnectionsDict = dict()
for sectionID in begEndDict:
	neighborList = neighborDict[sectionID]
	
	connections = [-1]*2
	for (neighID, thisPort, otherPort) in neighborList:
		(sectionType, sectionDict) = hornDict.get(neighID);
#		if sectionType == 'wall':
#			connections[thisPort - 1] = begEndDict[neighID][1]
		if sectionType in geometryHandlers:
			connections[thisPort - 1] = begEndDict[neighID][otherPort - 1]
	
	(sectionType, sectionDict) = hornDict.get(sectionID)
	if sectionType == "mouth":
		print(connections)
		connections[1] = 0
		
	begEndConnectionsDict[sectionID] = connections

print("dumping beginning and end cell connections dictionary")
print(begEndConnectionsDict)

#write simulation input file
for sectionID in hornDict.keys():
	print("processing section", sectionID)
	#check if this section is just geometry
	(sectionType, sectionDict) = hornDict.get(sectionID);
	print("processing section", sectionID, "(" + sectionType + ")")
	
	if sectionType in geometryHandlers:
		#this is geometry, use handler
		elementList = geometryHandlers[sectionType](dx, sectionDict)
		
		#for simple case, rear wall element list needs to be reversed

		(area1, area2, damping) = elementList[0]
		(beg, end) = begEndDict[sectionID]
		connections = begEndConnectionsDict[sectionID]
		prevElID = connections[0]
		prevNegList = [(str(prevElID), area1)]
		if prevElID == -1:
			prevNegList = []
		
		writeElem(str(beg), prevNegList, [(str(currElID), area2)], damping)
		lastElID = beg
		
		for (area1, area2, damping) in elementList[1:-2]:
			nextElID = currElID + 1
			writeElem(str(currElID), [(str(lastElID), area1)], [(str(nextElID), area2)], damping)
			lastElID = currElID
			currElID = nextElID;

		(area1, area2, damping) in elementList[-2]
		nextElID = end
		writeElem(str(currElID), [(str(lastElID), area1)], [(str(nextElID), area2)], damping)
		lastElID = currElID
		currElID += 1

		(area1, area2, damping) = elementList[-1]			
		nextElID = connections[1]
		nextPosList = [(str(nextElID), area2)]
		if nextElID == -1:
			nextPosList = []
			
		writeElem(str(end), [(str(lastElID), area1)], nextPosList, damping)
		
	elif sectionType == "speaker":
		hElemFile.write("s\n")
		neighborList = neighborDict[sectionID]
		print(neighborList)

		def getNeighborID(neighborList, begEndDict, index):
			for (neigh, myPort, neighPort) in neighborList:
				if myPort==index:
					(beg, end) = begEndDict[neigh]
					begEnd=[beg, end]
					elem=begEnd[neighPort-1]
					return elem
			return -1
		
		hElemFile.write("- " + str(getNeighborID(neighborList, begEndDict, 1)) + " " + str(sectionDict["A1"]))
		hElemFile.write("\n")
		hElemFile.write("+ " + str(getNeighborID(neighborList, begEndDict, 2)) + " " + str(sectionDict["A2"]))
		hElemFile.write("\n")

hElemFile.close();
print("fin.")
