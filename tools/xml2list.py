'''
parses XML file describing horn geometry
generates element set for simulation

output file format:

//volume element
e <#ID>				#element ID
A <AREA>			#cross section of the right side of the element
d <#VALUE>			#velocity damping
s <#ID>				#speaker and definition file
m <#ID>				#virtual microphone with ID


x <#VALUE>			#element length
'''

import xml.etree.ElementTree as ET
import math
import sys

import elemfile

infile = sys.argv[1]
strOutFile = sys.argv[2]
g_bVerbose = (len(sys.argv) == 4)

#function to check whether adjacent sections have non-matching cross-sections
def checkCrossSections(hornSections):
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
					
						key1 = "a" + portID
						key2 = "a" + neighborPortID
						if (key1 in sectionDict) and (key2 in neighborSectionDict):
							crossSect1 = sectionDict[key1]
							crossSect2 = neighborSectionDict[key2]
							if crossSect1 != crossSect2:
								print("WARNING: cross-sections do not match.", sectionID, key1, "->", neighborID, key2)
	#								else:
	#									print("cross-sections match!")
						else:
							print("did not find", key1, "in", sectionID, "or", key2, "in", neighborID)
	
	return neighborDict

# trace string of links
def traceChain(sUsed, neighborDict, chainStartID, iPort):
	# search for link to port iPort
	if g_bVerbose:
		print("tracing section", chainStartID, "port", iPort)
	
	nNeighbors = len(neighborDict[chainStartID])
	
	# check for fork or end section
	if nNeighbors != 2:
		# it's a fork element
		# or an end element
		# break the chain here 
		if g_bVerbose:
			print("section", chainStartID, "is an end section. terminating trace.")
		
		return []
	
	for (currentSectionID, lastPortID, currentPortID) in neighborDict[chainStartID]:
		if lastPortID == iPort:
			break

	if lastPortID != iPort:
		print("ERROR: port", iPort, "not found on section", chainStartID)
		
	if currentSectionID in sUsed:
		if g_bVerbose:
			print("section already processed", currentSectionID)
		
		return []
	
	# mark section as processed
	sUsed.add(currentSectionID)
	
	# the way forwand is not the way back...
	iFuturePortID = 3 - currentPortID
	
	if g_bVerbose:
		print("traced to section", currentSectionID, "port", currentPortID, "future port", iFuturePortID)
	
	# recurse
	lRecursionResult = traceChain(sUsed, neighborDict, currentSectionID, iFuturePortID)
	# append to result vector, save orientation
	lChain = [(currentSectionID, currentPortID==1)] + lRecursionResult
	
	# return result vector
	return lChain

def reverseChain(chain):
	aReversedChain = []
	
	for (chainSection, orientation) in reversed(chain):
		aReversedChain.append( (chainSection, not orientation) )
		
	return aReversedChain
	
# unravel neighbor dictionary
# find strings of linked sections
def unravelNeighbors(hornDict, neighborDict):
	# result vector
	aaChains = []
	
	sUsed = set()
	
	# for each section
	for sectionID in neighborDict.keys():
		# check if section was already processed
		if sectionID in sUsed:
			continue
		
		nNeighbors = len(neighborDict[sectionID])
		
		if nNeighbors == 1:
			continue
		
		# mark section as processed
		sUsed.add(sectionID)
		
		# check for fork section
		if nNeighbors == 3:
			# it's a fork element
			# break the chain here
			continue
			
		if g_bVerbose:
			print("starting trace at section", sectionID)
			
		# find string of linked sections in negative direction
		aChain1 = traceChain(sUsed, neighborDict, sectionID, 1)
		# find string in positive direction
		aChain2 = traceChain(sUsed, neighborDict, sectionID, 2)
		
		if g_bVerbose:
			print("chain 1:", aChain1)
			print("chain 1 reversesd:", reverseChain(aChain1))
		
		aChain = reverseChain(aChain1) + [ (sectionID, True) ] + aChain2
		
		# check for a speaker section
		for (section, bOrientation) in aChain:
			tag, sectionDict = hornDict[section]
			if tag == "speaker" and bOrientation == False:
				# reverse chain to create correct orientation for speaker
				aChain = reverseChain(aChain)
		
		aaChains.append(aChain)
		
		if g_bVerbose:
			print("trace result", aaChains[-1])
		

	#return result vector
	return aaChains

# escape a string to easily processible file name
def escapeString(strToEscape):
	return "".join([c if c.isalnum() else '_' for c in strToEscape ])

# discretizsation function
# return elements from A1 to A2 (including ends)
# one element longer than physical dimension
# in case of continuous sections, an element is clipped from the section

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

		elem = elemfile.Elem()
		elem.m_fArea = Ax
		elem.m_fDamping = damping
		outList.append(elem)
	
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
	
	positiveGradient = A2 > A1
		
	outList = [] 
	
	for iElem in range(nElems):
		relX=((iElem+1)/nElems) * xLen
		
		Ax=math.exp(relX + x1);
		
		if (Ax > A2) and positiveGradient:
			Ax = A2
		if (Ax < A1) and (not positiveGradient):
			Ax = A1
			
		elem = elemfile.Elem()
		elem.m_fArea = Ax
		elem.m_fDamping = damping
		
		outList.append(elem)
	
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
		elem = elemfile.Elem()
		elem.m_fArea = A1
		elem.m_fDamping = damping * iTransient / nTransientElems
		outList.append( elem )

	nWallElems = int((length / dx) + 1);
	
	for iElem in range(nWallElems):
		elem = elemfile.Elem()
		elem.m_fArea = A1
		elem.m_fDamping = damping
	
		outList.append( elem )
	
	#add break to the left
	outList[-1].m_bBreak = True

	return outList

def space_section(dx, params):
	#params should all be float
	A1 = params["a1"]
	
	length = params["length"]
	fraction = params["fraction"]
	
	nFreeElems = int((length / dx) + 1);

	outList = []
	
	r0 = math.sqrt(A1/math.pi)
	
	for iElem in range(nFreeElems):
		r = iElem * dx
		surf = math.pi * r * (math.pi*r0 + 2 * r)
		Ax = A1 + surf * fraction
		
		elem = elemfile.Elem()
		elem.m_fArea = Ax
		elem.m_bSpace = False
		
		outList.append(elem)

	outList[-1].m_strMic = "spl_mic"

	elem = elemfile.Elem()
	elem.m_fArea = outList[-1].m_fArea
	elem.m_iLink = 0
	elem.m_bSpace = False
	outList.append(elem)

	return outList

def speaker_section(dx, params):
	elem = elemfile.Elem()
	elem.m_fArea = params["a2"]
	elem.m_strSpeaker = escapeString(params["type"] )
	
	return [elem]

def mic_section(dx, params):
	elem = elemfile.Elem()
	elem.m_fArea = params["a2"]
	elem.m_strMic = escapeString(params["name"] )
	
	return [elem]

#dict of functions, working this way:
#[(area1, area2, damping)] = geometryHandlers["geom"](dx, params)
#where dx is the width of the elements
#return value is a list of the elements, sorted from neighbor1 to neighbor2
geometryHandlers = dict()
geometryHandlers["conical"] = conical_section
geometryHandlers["exponential"] = expo_section
geometryHandlers["wall"] = wall_section
geometryHandlers["space"] = space_section
#geometryHandlers["fork"] = dummy_section
geometryHandlers["mic"] = mic_section
geometryHandlers["speaker"] = speaker_section

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
	
	if section.tag=="tspset":
		#skip speaker
		continue	
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

#check whether the cross-sections given are discontinuous
neighborDict = checkCrossSections(hornDict)
sectionStrings = unravelNeighbors(hornDict, neighborDict)

# create empty element list (of class Element)
lElements = []

# (strElemID, iPort) -> iElemNumber
dStringEnds = dict()

# discretize continuous strings of sections
# for each string of sections
for sectionString in sectionStrings:
	lStringElems = []
	
	bFirstSection = True
	# for each section in string
	for (section, orientation) in sectionString:
		if g_bVerbose:
			print("processing section", section, "...")
		# discretize section
		# discretization result format: element list
		(strSectionTag, sectionDict) = hornDict[section]
		
		lSectionElems = geometryHandlers[strSectionTag](dx, sectionDict)
		if g_bVerbose:
			print("generated", len(lSectionElems), "elements on", strSectionTag, "id:", section)
		if len(lSectionElems) == 0:
			print("ERROR: no elements on", strSectionTag, "id:", sectionID)
				
		if not orientation:
			if g_bVerbose:
				print("reversing.")
			lSectionElems.reverse()
		
		# remove first element to create continuous slopes
		if not bFirstSection:
			lSectionElems = lSectionElems[1:]
		
		lStringElems += lSectionElems
	
	# add the "break link" property to the first element (after dummy) of the string
	lStringElems[0].m_bBreak = True
	
	lPaddedElems = lStringElems
	
	# create dummy element for first cross section
	if lStringElems[0].m_iLink == -1:
		begElem = elemfile.Elem()
		begElem.m_fArea = lStringElems[0].m_fArea
		begElem.m_bBreak = True
		
		lPaddedElems = [begElem] + lPaddedElems

	# add dummy element to the end if there is no link yet
	if lStringElems[-1].m_iLink == -1:
		endElem = elemfile.Elem()
		endElem.m_fArea = lStringElems[-1].m_fArea
	
		lPaddedElems += [endElem]
	
	# assign element numbers to elements
	lElements += lPaddedElems
	
	# append element numbers to end of string link list
	# append section IDs and link IDs to end of string link list
if g_bVerbose:
	print("writing element list to file", strOutFile)
elemfile.writeElemFile(strOutFile, lElements, dx)
   
# process links between sections
# for each end of string link
	# check if this is the A1 link of the fork
		# else discard
	# get destination string links
	# get destination element numbers
	# introduce link to destination elements


'''

def getNeighborXmlID(neighborList, index):
	for (neigh, myPort, neighPort) in neighborList:
		if myPort==index:
			return elem
	return None

def getNeighborElemID(neighborList, index):
#	print("looking for neighbor at port", index)
	for (neighID, myPort, neighPort) in neighborList:
		if myPort==index:
#			print("neighID", neighID, "neighPort", neighPort)
			lNeighElems = dElementLists[neighID]
			if len(lNeighElems) == 0:
				return None
			if neighPort == 1:
				(elID, A1, damping) = lNeighElems[0]
				return elID
			elif neighPort >= 2:
				(elID, A1, damping) = lNeighElems[-1]
				return elID
	return None

if g_bVerbose:
	print("dumping neighbor dictionary")
	print(neighborDict)

hElemFile=open(strOutFile, "wt")
hElemFile.write("dx " + str(dx) + "\n")

def escapeString(strToEscape):
	return "".join([c if c.isalnum() else '_' for c in strToEscape ])

#neighbors := [(id, area)]
def writeElem(elID, negNeighbors, posNeighbors, velDamp):
	#check if this is the special element 0
	if elID == 0:
		return
		
	hElemFile.write("e " + str(elID) )
	hElemFile.write("\n")
	for (negNeighbor, area) in negNeighbors:
		hElemFile.write("- " + str(negNeighbor) + " " + str(area))
		hElemFile.write("\n")
	for (posNeighbor, area) in posNeighbors:
		hElemFile.write("+ " + str(posNeighbor) + " " + str(area))
		hElemFile.write("\n")
		
	if velDamp != 0:
		hElemFile.write("d " + str(velDamp))
		hElemFile.write("\n")

#write simulation input file
for sectionID in hornDict.keys():
	#check if this section is just geometry
	(sectionType, sectionDict) = hornDict.get(sectionID)
	print("processing section", sectionID, "(" + sectionType + ")")
	
	neighborList = neighborDict.get(sectionID)
	
	if sectionType in geometryHandlers:
		lElements = dElementLists.get(sectionID)
	
		#link 0 is on the "-" side of the xml elements
		#link 1...n are on the "+" side

		print(sectionType, "id:", sectionID, "neighbors:", neighborList)
		minusID = getNeighborElemID(neighborList, 1)
		print(sectionType, "id:", sectionID, "minusID = ", minusID)
		
		#initialization if only one element exists
		(posElID, A1, posDamping) = lElements[0]
		lNegNeighbors = [ (minusID, A1) ]

		for iElement in range(len(lElements)-1):
			(elID, A1, A2, damping) = lElements[iElement]

			lNegNeighbors = []
			if minusID != None:
				lNegNeighbors = [ (minusID, A1) ]
				
			(posElID, posA1, posA2, posDamping) = lElements[iElement + 1]
			lPosNeighbors = [ (posElID, A2) ]
	
			for (negNeighID, unused) in lPosNeighbors:
				if negNeighID == 0:
					hElemFile.write("m \"" + escapeString(sectionID + " " + str(elID)) + "\" " + str(elID) + "\n")
				
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
		
		for (posNeighID, unused) in lPosNeighbors:
			if posNeighID == 0:
				hElemFile.write("m " + sectionID + "_" + str(posElID) + " " + str(posElID) + "\n")
				
		writeElem(posElID, lNegNeighbors, lPosNeighbors, posDamping)
		
		if sectionType == "mic":
			hElemFile.write("m \"" + escapeString(sectionDict["name"]) + "\" " + str(posElID))
			hElemFile.write("\n")

	elif sectionType == "speaker":
		hElemFile.write("s \"" + escapeString(sectionDict["type"] ) + "\"\n")
		print("speaker neighbors:", neighborList)

		hElemFile.write("- " + str(getNeighborElemID(neighborList, 1)) + " " + str(sectionDict["a1"]))
		hElemFile.write("\n")
		hElemFile.write("+ " + str(getNeighborElemID(neighborList, 2)) + " " + str(sectionDict["a2"]))
		hElemFile.write("\n")

hElemFile.close();
'''

print("xml2list: finished!")


