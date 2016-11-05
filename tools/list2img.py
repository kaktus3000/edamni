#!/usr/python3

#track chains of elements in the input file and draw a pretty image

from PIL import Image
import math
import sys
import elemfile

g_lSpeakerVectorGraphics = [[(0.0, 0.0),
							 (1.0, 0.0),
							 (0.6, 0.4),
							 (0.0, 0.4)],
							[(0.3, 0.4),
							 (0.3, 0.5)],
							[(0.0, 0.5),
							 (0.4, 0.5),
							 (0.4, 0.8),
							 (0.0, 0.8)]
							]

infile = sys.argv[1]
outfile = sys.argv[2]

aElems, dMics, dSpeakers, g_dx = elemfile.scanElemFile(infile)

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

maxDia = toDiam(fMaxArea)
print("max area is", fMaxArea, "diam", maxDia)

nGraphElems = len(aElems)

imgWidth = (int(maxDia/g_dx+2)//2)*2 + 2

image = Image.new("RGB", (imgWidth, (int(nGraphElems)//2)*2 + 2), "black")

hMappingFile=open(outfile + ".txt", "wt")

pixMap = image.load()

for pixel in range(nGraphElems):
	elem = aElems[pixel]

	hMappingFile.write(str(elem) + "\t" +  str(imgWidth // 2) + "\t" + str(pixel) + "\t" + str(imgWidth // 2) + "\n")
#	print(pixel, elem)
	
	area = elem.m_fArea
	
	x = toDiam(area)
	drawX = int(x/g_dx)
#	print(elem, elemID, area, x)
	pixMap[drawX, pixel] = (255,255,255)
	#mark infinite element
	'''
	if len(dElems[elem].positiveNeighbors) > 0:
		(neighID, unused) = dElems[elem].positiveNeighbors[0]
		if neighID == 0:
			for x in range(drawX):
				pixMap[x, pixel] = (255,0,255)
			continue
	
	#mark walls
	if len(dElems[elem].positiveNeighbors) == 0 or len(dElems[elem].negativeNeighbors) == 0:
		for x in range(drawX):
			pixMap[x, pixel] = (255,255,255)
		continue
	'''
	#mark damped elements
	if elem.m_fDamping != 0:
		for x in range(drawX):
			pixMap[x, pixel] = (0,127,0)

image.save(outfile)
hMappingFile.close()

print("fin.")
