#!/usr/python3

#track chains of elements in the input file and draw a pretty image

from PIL import Image
import math
import sys
import elemfile

g_lSpeakerVectorGraphics = [[(0.0, 0.0),
							 (0.0, 1.0),
							 (-0.2, 0.8),
							 (-0.2, 0.2)],
							[(-0.2, 0.6),
							 (-0.25, 0.6),
							 (-0.25, 0.4),
							 (-0.2, 0.4)],
							[(-0.25, 0.7),
							 (-0.25, 0.3),
							 (-0.4, 0.3),
							 (-0.4, 0.7)]
							]

def rasterizeLine(pixMap, vStart, vEnd, color):
	fSample = .5
	(x1, y1) = vStart
	(x2, y2) = vEnd
	
	fDx = x2 - x1
	fDy = y2 - y1
	
	fLength = math.sqrt(fDx * fDx + fDy * fDy)
	
	if fLength < 0.5:
		return
	
	fScan = fSample * 1.0 / fLength
	
	for iSample in range(int( 1.0 / fScan) ):
		x = x1 + fDx * iSample * fScan
		y = y1 + fDy * iSample * fScan 
		
		if pixMap[x, y] == (255, 255, 255):
			pixMap[x, y] = color

infile = sys.argv[1]
outfile = sys.argv[2]
iWidth  = int(sys.argv[3])
iHeight = int(sys.argv[4])
bOnlyGeometry = sys.argv[5] == "1"

aElems, dMics, dSpeakers, g_dx = elemfile.scanElemFile(infile)

aGeomOnly = []
if bOnlyGeometry:
	for elem in aElems:
		if elem.m_bGeom:
			aGeomOnly.append(elem)
	aElems = aGeomOnly

#now create a nice image
fMaxArea = 0
for elem in aElems:
	# print(elem)
	fMaxArea = max(fMaxArea, elem.m_fArea)

def toDiam(area):
	if area > 0:
		return math.sqrt(area/math.pi) * 2.0
	else:
		return 0

nGraphElems = len(aElems)
maxDia = toDiam(fMaxArea)
print("list2img: number of elements:", nGraphElems, "; max area:", fMaxArea, "; diam:", maxDia)

image = Image.new("RGB", (iWidth, iHeight), "white")

#hMappingFile=open(outfile + ".txt", "wt")

pixMap = image.load()

fRelativeHeight = maxDia / (nGraphElems * g_dx) * iWidth

print("list2img: relative height:", fRelativeHeight)

if fRelativeHeight > iHeight:
	iWidth *= iHeight / fRelativeHeight
	
	print("list2img: scaling width to:", iWidth)
else:
	iHeight = fRelativeHeight
	print("list2img: scaling height to:", iHeight)

fWidthNormalizer  = 1.0 / nGraphElems * (iWidth - 1)
fHeightNormalizer = 1.0 / maxDia * (iHeight - 1)

fMaxDamping = 0.1
for iElem in range(nGraphElems):
	fMaxDamping = max(fMaxDamping, aElems[iElem].m_fDamping)

for iElem in range(nGraphElems):

	#hMappingFile.write(str(elem) + "\t" +  str(imgWidth // 2) + "\t" + str(pixel) + "\t" + str(imgWidth // 2) + "\n")
#	print(pixel, elem)

	xEnd   = iElem  * fWidthNormalizer
	yEnd   = toDiam(aElems[iElem].m_fArea) * fHeightNormalizer
	
	#mark speaker
	if aElems[iElem].m_strSpeaker != "":
		for chain in g_lSpeakerVectorGraphics:
			for iLine in range(len(chain)):
				(x0, y0) = chain[iLine - 1]
				xLine0 = x0 * yEnd
				yLine0 = (y0 - 0.5) * yEnd
			
				(x1, y1) = chain[iLine]
				xLine1 = x1 * yEnd
				yLine1 = (y1 - 0.5) * yEnd
			
				# clamp graphics
				xLine0 = max(-xEnd, xLine0)
				xLine1 = max(-xEnd, xLine1)
				
				rasterizeLine(pixMap, (xLine0 + xEnd, yLine0 + iHeight * 0.5), (xLine1 + xEnd, yLine1 + iHeight * 0.5), (255,0,0))
		
	#mark links
	if aElems[iElem].m_iLink != -1:
		rasterizeLine(pixMap, (xEnd, (yEnd + iHeight) * 0.5), (xEnd, (-yEnd + iHeight) * 0.5), (255,0,255) )
		
	#mark mic
	if aElems[iElem].m_strMic != "":
		rasterizeLine(pixMap, (xEnd, (yEnd + iHeight) * 0.5), (xEnd, (-yEnd + iHeight) * 0.5), (0,127,255) )
	
	#mark sink elements
	if aElems[iElem].m_fSink != 1.0:
		rasterizeLine(pixMap, (xEnd, (yEnd + iHeight) * 0.5), (xEnd, (-yEnd + iHeight) * 0.5), (127,0,255) )
	
	#mark not geometry
	if not aElems[iElem].m_bGeom:
		rasterizeLine(pixMap, (xEnd, (yEnd + iHeight) * 0.5), (xEnd, (-yEnd + iHeight) * 0.5), (224, 224, 224) )	
	
	# draw outline
	if iElem > 1:
	
		xStart = (iElem-1) * fWidthNormalizer
		yStart = toDiam(aElems[iElem-1].m_fArea) * fHeightNormalizer

		rasterizeLine(pixMap, (xStart, (yStart + iHeight) * 0.5), (xEnd, (yEnd + iHeight) * 0.5), (0,0,0) )
		rasterizeLine(pixMap, (xStart, (-yStart + iHeight) * 0.5), (xEnd, (-yEnd + iHeight) * 0.5), (0,0,0) )

	#mark damped elements
	fDamping = aElems[iElem].m_fDamping
	if fDamping != 0:
		fRelativeDamping = min (fDamping / fMaxDamping, 1)
	
		color = (int(255 * (1.0 - fRelativeDamping)), int(127 + (1.0 - fRelativeDamping) * 128), int(255 * (1.0 - fRelativeDamping)) )

		rasterizeLine(pixMap, (xEnd, (yEnd + iHeight) * 0.5), (xEnd, (-yEnd + iHeight) * 0.5), color)


print("list2img: writing image", outfile)

#draw center line
rasterizeLine(pixMap, (0, iHeight / 2), (iWidth - 1, iHeight / 2), (0,0,0) )

image.save(outfile)
#hMappingFile.close()

