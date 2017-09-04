# calculate length distribution files for input element file

import elemfile
import sys

def getDistribution():
	lDistribution = [-.05, -.03, -.02, -.01, -.005,
				0.0, 0.0,
				.005, .01, .02, .03, .05]
	return lDistribution

def lengthVariation(strInFile, strOutFile, fPercentage):

	strFilename = sys.argv[1]

	aElems, dMics, dSpeakers, dx = elemfile.scanElemFile(strFilename)

	nGeomElems = 0

	for iElem in range(len(aElems)):
		if aElems[iElem].m_bGeom:
			nGeomElems += 1

	nElements = fPercentage * nGeomElems

	aVariedElems = []

	iGeomElems = 0

	for elem in aElems:
		if elem.m_bGeom and elem.m_iLink==-1 and elem.m_strSpeaker=="" and elem.m_strMic=="":
			continue

		if float(iGeomElems) * fPercentage > 1:
			print("variation: duplicating geom elem", iGeomElems)
			aVariedElems.append(elem)
			iGeomElems = 0
	
		if iGeomElems * fPercentage < -1:
			print("variation: erasing geom elem", iGeomElems)
			iGeomElems = 0
		else:
			aVariedElems.append(elem)

		iGeomElems += 1		
		
	elemfile.writeElemFile(strOutFile, aVariedElems, dx)
