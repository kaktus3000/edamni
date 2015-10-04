'''
parses XML file describing horn geometry
generates element set for simulation

output file format:

//volume element
e <#ID>				#element ID
- <#REF> <AREA>		#volume id of "negative" side adjacent elements and common cross-section
+ <#REF> <AREA>		#same for "positive" side
d <#VALUE>			#velocity damping

//speaker
s					#speaker with left and right adjacent elements, definition file
- <#REF> <AREA>		#volume id of left adjacent elements and common cross-section
+ <#REF> <AREA>		#same for right

m <#ID> <#REF>		#virtual microphone ID and reference to measured element
dx <#VALUE>			#element width

'''

import xml.etree.ElementTree as ET
import math
import sys

infile = sys.argv[1]
outfile = sys.argv[2]
g_bVerbose = (len(sys.argv) == 4)

#function to check whether adjacent sections have non-matching cross-sections
def check_cross_sections(hornSections):
	#dictionary for neighbor links
	#ID1 -> (ID2, port1, port2)
	neighborDict = dict()
	
	for sectionID in hornSections.keys():
		(sectionType, sectionDict) = hornSections[sectionID]
#		print("checking section", sectionID, "(" + sectionType + ")")
		#check neighbors
		#(neighborID, portID)
		lNeighbors = []
		for propertyName in sectionDict.keys():
			propValue = sectionDict[propertyName]
#			print("checking property", propertyName)
			#see whether we have a connection to that branch
			if propertyName.find("neighbor") >=0:
				lNeighbors.append( (propValue, propertyName.replace("neighbor", "") ) )
#				print("found link to neighbor", neighborID, ", connected to port", portID)
				
		#scan neighbors
		for (neighborID, portID) in lNeighbors:
			(neighborSectionType, neighborSectionDict) = hornSections[neighborID]
			#now locate the link back to this section on the neighbor to get its port
			for neighborPropertyName in neighborSectionDict.keys():
				neighborPropValue = neighborSectionDict[neighborPropertyName]
#				print("checking neighbor property", neighborPropertyName)
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


#outputs:
#(A1, A2, damp)

#area = 0 denotes closed end
#area = inf denotes open end

def conical_section(dx, params):
	#params should all be float
	A1 = params["a1"]
	A2 = params["a2"]
	
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
	A1 = params["a1"]
	A2 = params["a2"]
	length = params["length"]
	damping = params["damping_constant"]
	
	nElems = int((length / dx) + 1);
	
	x1 = math.log(A1)
	x2 = math.log(A2)
	
	xLen = x2-x1;
	
	lastA = A1
	positiveGradient = A2 > A1
		
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
	A1 = params["a1"]
	
	length = params["damping_thickness"]
	damping = params["damping_constant"]
	transient = params["damping_transient"]

	outList = []

	nTransientElems = int((transient / dx) + 1);
	for iTransient in range(nTransientElems):
		outList.append( (A1, A1, damping * iTransient / nTransientElems ) )

	nWallElems = int((length / dx) + 1);
	outList.extend( [(A1, A1, damping)]*nWallElems )

	return outList

def space_section(dx, params):
	#params should all be float
	A1 = params["a1"]
	
	length = params["length"]
	fraction = params["fraction"]
	
	nFreeElems = int((length / dx) + 1);
	
	lastA = A1
	outList = []
	
	r0 = math.sqrt(A1/math.pi)

	for iElem in range(nFreeElems):
		r = iElem * dx
		surf = math.pi * r * (math.pi*r0 + 2 * r)
		Ax = A1 + surf * fraction
		
		outList.append((lastA, Ax, 0))
		lastA = Ax

	outList.append( (lastA, -1, 0) )

	return outList

def dummy_section(dx, params):
	#params should all be float
	A1 = params["a1"]
	outList = [(A1, A1, 0)]
	
	return outList

#dict of functions, working this way:
#[(area1, area2, damping)] = geometryHandlers["geom"](dx, params)
#where dx is the width of the elements
#return value is a list of the elements, sorted from neighbor1 to neighbor2
geometryHandlers = dict()
geometryHandlers["conical"] = conical_section
geometryHandlers["exponential"] = expo_section
geometryHandlers["wall"] = wall_section
geometryHandlers["space"] = space_section
geometryHandlers["fork"] = dummy_section

tree = ET.parse(infile)
horn = tree.getroot()

if horn.tag != "horn":
	print("malformed xml: root elem has to be horn!")
	exit();
	
dx = float(horn.attrib["dx"])
#print("dx =", dx)

hornDict = dict()
#print("dumping xml input")

#IDs for elements
wallID = 0
currElID = 1

dElementLists = dict()

for section in horn:
	if not "id" in section.attrib:
		print("malformed xml: elem", section.tag, "has no 'id' attribute!")
#	print(section.tag, "(" + section.attrib["id"] + ")")
	sectionID = section.attrib["id"]
	
	sectionDict = dict()
	
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
		sectionDict[elem.tag] = elemText
		
	hornDict[sectionID] = (section.tag, sectionDict)

	#generate elements on this section
	elementList = []
	if section.tag in geometryHandlers:
		#this is geometry, use handler
#		print(section.tag, sectionDict)
		elementList = geometryHandlers[section.tag](dx, sectionDict)
		print("generated", len(elementList), "elements on", section.tag, "id:", sectionID)
		if len(elementList) == 0:
			print("error, no elements on", section.tag, "id:", sectionID)

	dElementLists[sectionID] = []
	for (A1, A2, damping) in elementList:
		elID = currElID
		if A1 == -1 or A2 == -1:
			elID = wallID
		else:
			currElID += 1

		#assign id to element
		dElementLists[sectionID].append( (str(elID), A1, A2, damping) )

#check whether the cross-sections given are discontinuous
neighborDict = check_cross_sections(hornDict)

def getNeighborXmlID(neighborList, index):
	for (neigh, myPort, neighPort) in neighborList:
		if myPort==index:
			return elem
	return None

def getNeighborElemID(neighborList, index):
	print("looking for neighbor at port", index)
	for (neighID, myPort, neighPort) in neighborList:
		if myPort==index:
			print("neighID", neighID, "neighPort", neighPort)
			lNeighElems = dElementLists[neighID]
			if len(lNeighElems) == 0:
				return None
			if neighPort == 1:
				(elID, A1, A2, damping) = lNeighElems[0]
				return elID
			elif neighPort >= 2:
				(elID, A1, A2, damping) = lNeighElems[-1]
				return elID
	return None

if g_bVerbose:
	print("dumping neighbor dictionary")
	print(neighborDict)

hElemFile=open(outfile, "wt")
hElemFile.write("dx " + str(dx) + "\n")

#neighbors := [(id, area)]
def writeElem(elID, negNeighbors, posNeighbors, velDamp):
	hElemFile.write("e " + str(elID) )
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

#write simulation input file
for sectionID in hornDict.keys():
	#check if this section is just geometry
	(sectionType, sectionDict) = hornDict.get(sectionID)
	print("processing section", sectionID, "(" + sectionType + ")")
	
	if sectionType in geometryHandlers:
		lElements = dElementLists.get(sectionID)
		neighborList = neighborDict.get(sectionID)

		#link 0 is on the "-" side of the xml elements
		#link 1...n are on the "+" side

		print(sectionType, "id:", sectionID, "neighbors:", neighborList)
		minusID = getNeighborElemID(neighborList, 1)
		print(sectionType, "id:", sectionID, "minusID = ", minusID)

		for iElement in range(len(lElements)-1):
			(elID, A1, A2, damping) = lElements[iElement]

			lNegNeighbors = []
			if minusID != None:
				lNegNeighbors = [ (minusID, A1) ]

			(posElID, posA1, posA2, posDamping) = lElements[iElement + 1]
			lPosNeighbors = [ (posElID, A2) ]
	
			#check if we write the special element 0
			if elID != 0:
				writeElem(elID, lNegNeighbors, lPosNeighbors, damping)

			lNegNeighbors = [ (elID, A2) ]
			
			minusID = elID

		lPosNeighbors = []
		for portIndex in range(2, len(neighborList) + 1):
			posID = getNeighborElemID(neighborList, portIndex)
			if posID!=None:
				#only continue if this section has a positive neighbor elem
				#if there is a speaker, do nothing
				area = sectionDict["a" + str(portIndex)]
				lPosNeighbors.append( (posID, area) )

		print("neighbor list:", neighborList)
		print("positive neighbors:", lPosNeighbors)
		writeElem(posElID, lNegNeighbors, lPosNeighbors, posDamping)

	elif sectionType == "speaker":
		hElemFile.write("s " + sectionDict["type"] + "\n")
		neighborList = neighborDict[sectionID]
		print("speaker neighbors:", neighborList)

		hElemFile.write("- " + getNeighborElemID(neighborList, 1) + " " + str(sectionDict["a1"]))
		hElemFile.write("\n")
		hElemFile.write("+ " + getNeighborElemID(neighborList, 2) + " " + str(sectionDict["a2"]))
		hElemFile.write("\n")

hElemFile.close();
print("fin.")
