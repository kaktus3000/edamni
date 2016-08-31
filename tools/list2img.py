#!/usr/python3

#track chains of elements in the input file and draw a pretty image

from PIL import Image
import math
import sys

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

dElems, dMics, dSpeakers, dx = elemfile.scanElemFile(infile)
		
sVisited = set()

#build directed graph from speaker
#search positive direction
def subGraph(dElems, elem, currGraph):
	#there should be only one direction to go
	currGraph.append(elem)
		
	if len(dElems[elem].positiveNeighbors) > 0:
		(elem, area) = dElems[elem].positiveNeighbors[0]
	else:
		(elem, area) = dElems[elem].negativeNeighbors[0]
	
	while(elem > 0):
#		print("lastElem:", lastElem, "elem:", elem, "neg:", dElems[elem].negativeNeighbors, "pos:", dElems[elem].positiveNeighbors)

		if elem in sVisited:
			return currGraph
		sVisited.add(elem)

		bFound = False
		for (neighID, area) in dElems[elem].positiveNeighbors:
			if neighID in currGraph:
				bFound = True
		
		neighs = []

		if bFound:
			neighs = dElems[elem].negativeNeighbors
		else:
			neighs = dElems[elem].positiveNeighbors

		nNeighs = len(neighs)
#		print("elem", elem, dElems[elem], "has", nNeighs, "neighs")
		currGraph.append(elem)

		if nNeighs == 0:
			return currGraph
		if nNeighs == 1:
			(elemID, area) = neighs[0]
#			print(neighs)
			elem = elemID
			continue
		#more than two
		print(">1")
		exit(0)
		subGraphs = []
		for neigh in neighs:
			(elemID, area) = neigh
			subGraphs.append(subGraph(dElems, elemID, positiveDir, []) )
		return currGraph.append(subGraphs)
	
	return currGraph

print(speakers[0])
negGraph = subGraph(dElems, speakers[0].negativeElem, [])
posGraph = subGraph(dElems, speakers[0].positiveElem, [])

negGraph.reverse()

graph = negGraph + posGraph
#print(posGraph)

#now create a nice image
maxArea = 0
for elem in dElems.values():
	for (elemID, area) in elem.positiveNeighbors:
		maxArea = max(maxArea, area)

def toDiam(area):
	return math.sqrt(area/math.pi) * 2.0

maxDia = toDiam(maxArea)
print("max area is", maxArea, "diam", maxDia)

nGraphElems = len(graph)

imgWidth = (int(maxDia/g_dx+2)//2)*2 + 2

image = Image.new("RGB", (imgWidth, (int(nGraphElems)//2)*2 + 2), "black")

hMappingFile=open(outfile + ".txt", "wt")

pixMap = image.load()

print("first elem:", graph[0])
print("first elem neighs:", dElems[graph[0]].positiveNeighbors)

print("last elem:", graph[-1])
print("last elem neighs:", dElems[graph[-1]].positiveNeighbors)

for pixel in range(nGraphElems):
	elem = graph[pixel]

	hMappingFile.write(str(elem) + "\t" +  str(imgWidth // 2) + "\t" + str(pixel) + "\t" + str(imgWidth // 2) + "\n")
#	print(pixel, elem)
	neighbors = dElems[elem].positiveNeighbors
	if neighbors == []:
		neighbors = dElems[elem].negativeNeighbors
	(elemID, area) = neighbors[0]
	x = toDiam(area)
	drawX = int(x/g_dx)
#	print(elem, elemID, area, x)
	pixMap[drawX, pixel] = (255,255,255)
	#mark infinite element
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
	#mark damped dElems
	if dElems[elem].damping != 0:
		for x in range(drawX):
			pixMap[x, pixel] = (0,127,0)

image.save(outfile)
hMappingFile.close()

print("fin.")
