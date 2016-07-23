import numpy
import sys
import os
import configparser

import elemfile

g_strDir = sys.argv[1]
g_strSimuInputFile = sys.argv[2]

config = configparser.ConfigParser()

config.read(g_strDir + g_strSimuInputFile)
g_strSimuOutputFile = g_strDir + config.get("general", "output_file")
g_strElementFile = g_strDir + config.get("general", "element_file")

dElems, dMics, dSpeakers, dx = elemfile.scanElemFile(g_strElementFile)

# get max element ID
aIDs = []

#look for links to element 0, this will be the infinite element
g_nInfinteElements = 100

aInfiniteElementIndices = []

#factors will first be filled with areas
iVelocityElement = 0
aVelocity1stIndices = []
aVelocity1stFactors = []
aVelocity2ndIndices = []
aVelocity2ndFactors = []

# [id] -> set(id1, id2, ...)
dConnections = dict()

for iID in dElems.keys():
	aIDs.append(iID)

	neighbors = []
	for target, area in dElems[iID].negativeNeighbors:
		neighbors.append( (target, area, -1) )
	for target, area in dElems[iID].positiveNeighbors:
		neighbors.append( (target, area, 1) )
	
	aVelocityElements = []
	
	for target, area, sign in neighbors:
		if iID in dConnections:
			if target in dConnections[iID]:
				continue
		else:
			dConnections[iID] = set()
		if not target in dConnections:
			dConnections[target] = set()
	
		aVelocity1stIndices.append(iID)
		aVelocity1stFactors.append(-1 * sign * area)
		aVelocity2ndIndices.append(target)
		aVelocity2ndFactors.append(sign * area)
		
		aVelocityElements.append(iVelocityElement)
		iVelocityElement += 1
		
		dConnections[iID].add(target)
		dConnections[target].add(iID)
		
		if target == 0:
			for iElement in range(g_nInfinteElements):
				break
	
nPressureElems = numpy.max(aIDs) + 1

print("number of elements:", nPressureElems - 1)

aPressure1stIndices = [0] * nPressureElems
aPressure1stFactors = [0] * nPressureElems
aPressure2ndIndices = [0] * nPressureElems
aPressure2ndFactors = [0] * nPressureElems
aPressure3rdIndices = [0] * nPressureElems
aPressure3rdFactors = [0] * nPressureElems

#iterate velocity elements to fill pressure factors
for index in range(len(aVelocity1stIndices)):
	aConnections =  [(aVelocity1stIndices[index], aVelocity1stFactors[index]), (aVelocity2ndIndices[index], aVelocity2ndFactors[index])]
	
	for (iID, fFactor) in aConnections:
		#print("pressure elem", iID, "-> velocity elem", index)
		if aPressure1stIndices[iID] == 0:
			aPressure1stIndices[iID] = index
			aPressure1stFactors[iID] = fFactor
		elif aPressure2ndIndices[iID] == 0:
			aPressure2ndIndices[iID] = index
			aPressure2ndFactors[iID] = fFactor
		elif aPressure3rdIndices[iID] == 0:
			aPressure3rdIndices[iID] = index
			aPressure3rdFactors[iID] = fFactor
		else:
			print("ERROR: more than three connections for element", iID)
		
print(aPressure1stIndices)
print(aPressure2ndIndices)
print(aPressure3rdIndices)

#each element is a pressure element
#each link between the elements is a velocity element

g_fTimeStep = 0.2*dx/numpy.sqrt(container->info->gasconstant*container->info->temperature);
