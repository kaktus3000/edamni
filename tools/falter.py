# fold horn in a graphocal way. tries to fold in the upwards direction

import elemfile
import sys
import math
import numpy
import copy
from PIL import Image

fWidth=.5
fMinRadius = 1.5
fMinWall = .05
fAngleStep = math.pi / 180.0 * 10
fMinPlace = .9
fDepth = .06


strFilename = sys.argv[1]

aElems, dMics, dSpeakers, dx = elemfile.scanElemFile(strFilename)

fResolution=dx/2
print("falter: resolution %f" % fResolution)

afAreas=[]

for iElem in range(len(aElems)):
	if aElems[iElem].m_bGeom:
		afAreas.append(aElems[iElem].m_fArea)

# calculated in pixels
npaHornWidth = numpy.asarray(afAreas) / (fDepth * fResolution)

npaMinRadii = fMinRadius * npaHornWidth

fMinWallPixels = fMinWall / fResolution

iWidth = int(fWidth / fResolution) + 1
iHeight = int (len(afAreas) + numpy.amax(npaHornWidth) * .5) +1

print("falter: image size (%d, %d)" % (iWidth, iHeight))

npaInitialMap = numpy.zeros((iWidth, iHeight))

def placePixel(npaMap, x,y):
	x = int(x)
	y = int(y)
	
	w,h = npaMap.shape
	if x>=0 and x<w and y>=0 and y<h:
		npaMap[x][y]=1
		
def testPixel(npaMap, x,y):
	x = int(x)
	y = int(y)
		
	w,h = npaMap.shape
	if x>=0 and x<w and y>=0 and y<h:
		if npaMap[x][y] == 0:
			return True
	
	return False

placePixel(npaInitialMap, iWidth/2, iHeight/2)

def saveMap(npaMap, strFileName):
	image = Image.new("L", (iWidth, iHeight), "black")
	pixMap = image.load()
	for x in range(iWidth):
		for y in range(iHeight):
			if npaMap[x][y] > 0:
				pixMap[x,y]=255
				
	image.save(strFileName)

def placeVertex(iVertex, iDecision, npaPrevVertex, npaDirection, iDirection, npaImage):
	# test if we can place the cross section
	npaVertex = npaPrevVertex + npaDirection
	
	#print("placing vertex", iVertex, "at", npaVertex)
	
	npaPerpendicular = numpy.asarray([-npaDirection[1], npaDirection[0] ])
	
	fWidth = npaHornWidth[iVertex]
	
	#print("width", fWidth)
	
	nPlaceable = 0
	nTested = 0
	
	for iPixel in range(int(fWidth) + 1):
		vPos = (iPixel - .5 * fWidth) * npaPerpendicular + npaVertex
		# test position
		#print("testing pixel", vPos)
		if testPixel(npaImage, vPos[0], vPos[1]):

			nPlaceable += 1
		nTested += 1
		
	#print("placing test:", nPlaceable, "(" + str(nTested) + ")")
	
	fPlaceRatio = (nPlaceable+1) / nTested
	if fPlaceRatio < fMinPlace:
		# failed to place the vertex due to constraint violation
		return False
		
	# is it the last point?
	if iVertex == len(afAreas) - 1:
		# we're done
		
		# measure vertical extent of horn
		# save configuration
		return True

	# place wall geometry in map
	npaNewImage = copy.copy(npaImage)
	
	for iPixel in range(int(fMinWallPixels)+1):
		vPos = (iPixel + .5 * fWidth + fMinWallPixels) * npaPerpendicular + npaVertex
		placePixel(npaNewImage, vPos[0], vPos[1])
		vPos = (- iPixel - .5 * fWidth - fMinWallPixels) * npaPerpendicular + npaVertex
		placePixel(npaNewImage, vPos[0], vPos[1])
	
	print("iDecision", iDecision)
	# check if we have to decide a direction yet
	if iDecision > 0:
		placeVertex(iVertex + 1, iDecision-1, npaVertex, npaDirection, npaNewImage)
		
		return True
		
	print("decision at vertex", iVertex)
		
	saveMap(npaImage, "falter" + str(iVertex) + ".png")
	# calculate bending angle
	
	vDirections = []
	yDirections = []
	# calculate direction vectors
	for fAngle in [-2.5*numpy.pi / 180, 0, 2.5*numpy.pi / 180]:
		fCurrentAngle = math.atan2(npaDirection[0], npaDirection[1])
		
		fTotalAngle = fCurrentAngle + fAngle
		
		vDir = numpy.asarray([math.sin(fTotalAngle), math.cos(fTotalAngle)])
		vDirections.append( vDir)
		
		yDirections.append(vDir[1])
		
	nDirections = len(vDirections)
	
	#print(vDirections)
	
	# first priority: follow same direction as before
	# second priority: go up
	# third priority: go down
	
	# sort allowable angles by y component
	npaSortIndices = numpy.argsort(yDirections)
	
	# test allowable angles
	for iDirection in range(nDirections):	
		# place next section
		print("fWidth", fWidth, "fResolution", fResolution)
		placeVertex(iVertex + 1, int(fWidth), npaVertex, vDirections[iDirection], npaNewImage)

saveMap(npaInitialMap, "falter.png")

# fold horn
placeVertex(0, 0, numpy.asarray([iWidth -1, 15]), numpy.asarray([-1, 0]), npaInitialMap)

