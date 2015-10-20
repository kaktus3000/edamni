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

class Elem:
#	def __init__(self, name):
#		self.negativeNeighbors = []
#		self.tricks = []    # creates a new empty list for each dog
	negativeNeighbors = []; #tuple: id, area
	positiveNeighbors = [];
	damping = 0;
	def __str__(self):
		return "{element; neg:" + str(self.negativeNeighbors) + "; pos:" + str(self.positiveNeighbors) + "; damp:" + str(self.damping) + "}"

class Microphone:
	dummy = 0

class Speaker:
	positiveElem = -1;
	negativeElem = -1;
	def __str__(self):
		return "{speaker; neg:" + str(self.negativeElem) + "; pos:" + str(self.positiveElem) + "}"

elems = dict()

f = open(infile, 'r')

aLines = f.readlines()

f.close()

#delta X of the elements (length)
g_dx = 0.01

iLine = 0

def scanAttribs(aLines, iLine):
	negativeNeighbors = []
	positiveNeighbors = []
	damping = 0

	bLineForElem = True
	while(iLine < len(aLines)):
		currLine = aLines[iLine]
		attribType = currLine[0]
#		print("attribute type is", attribType)
		if attribType == "-":
			substrings = currLine.split(" ")
#			print("substrings are:", substrings)
			conn = int(substrings[1])
			area = float(substrings[2])
			negativeNeighbors.append( (conn, area) )
		elif attribType == "+":
			substrings = currLine.split(" ")
#			print("substrings are:", substrings)
			conn = int(substrings[1])
			area = float(substrings[2])
			positiveNeighbors.append( (conn, area) )
		elif attribType == "d":
			damping = float(currLine[2:])
		else:
			break
		iLine += 1
	return (negativeNeighbors, positiveNeighbors, damping, iLine -1)

speakers = []

while iLine < len(aLines):
	currLine = aLines[iLine]
	linetype = currLine[0]

#	print ("type of line", iLine, "is", linetype)

	if linetype == "e":
		elID = int(currLine[2:])
#		print("element ID is", elID)
		(negN, posN, damp, line) = scanAttribs(aLines, iLine + 1)

		elem = Elem()
		elem.negativeNeighbors = negN
		elem.positiveNeighbors = posN
		elem.damping = damp
		elems[elID] = elem
		iLine = line
	elif linetype == "s":
#		print("speaker!")
		(negN, posN, damp, line) = scanAttribs(aLines, iLine + 1)

		spkr = Speaker()
		(spkr.positiveElem, unused) = posN[0]
		(spkr.negativeElem, unused) = negN[0]
#		spkr.positiveElem = posN[0]
#		spkr.negativeElem = negN[0]

		speakers.append(spkr)
		iLine = line
	elif linetype == "m":
		micID = int(currLine[2:])
#		print("mic ID", micID)
	elif linetype == "d":
		#HACK: this is the 'dx' element
		g_dx = float(currLine[3:])
		print("element length is", g_dx)
	else:
		print("type of line not recognized!", currLine)
	iLine += 1

#for elem in elems:
#	print(elem, "->", elems[elem])

#build directed graph from speaker
#search positive direction
def subGraph(elems, elem, currGraph):
	#there should be only one direction to go
	currGraph.append(elem)
	
	if len(elems[elem].positiveNeighbors) > 0:
		(elem, area) = elems[elem].positiveNeighbors[0]
	else:
		(elem, area) = elems[elem].negativeNeighbors[0]
	
	while(elem > 0):
#		print("lastElem:", lastElem, "elem:", elem, "neg:", elems[elem].negativeNeighbors, "pos:", elems[elem].positiveNeighbors)

		bFound = False
		for (neighID, area) in elems[elem].positiveNeighbors:
			if neighID in currGraph:
				bFound = True
		
		neighs = []

		if bFound:
			neighs = elems[elem].negativeNeighbors
		else:
			neighs = elems[elem].positiveNeighbors

		nNeighs = len(neighs)
#		print("elem", elem, elems[elem], "has", nNeighs, "neighs")
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
			subGraphs.append(subGraph(elems, elemID, positiveDir, []) )
		return currGraph.append(subGraphs)
	
	return currGraph

print(speakers[0])
negGraph = subGraph(elems, speakers[0].negativeElem, [])
posGraph = subGraph(elems, speakers[0].positiveElem, [])

negGraph.reverse()

graph = negGraph + posGraph
#print(posGraph)

#now create a nice image
maxArea = 0
for elem in elems.values():
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
print("first elem neighs:", elems[graph[0]].positiveNeighbors)

print("last elem:", graph[-1])
print("last elem neighs:", elems[graph[-1]].positiveNeighbors)

for pixel in range(nGraphElems):
	elem = graph[pixel]

	hMappingFile.write(str(elem) + "\t" +  str(imgWidth // 2) + "\t" + str(pixel) + "\t" + str(imgWidth // 2) + "\n")
#	print(pixel, elem)
	neighbors = elems[elem].positiveNeighbors
	if neighbors == []:
		neighbors = elems[elem].negativeNeighbors
	(elemID, area) = neighbors[0]
	x = toDiam(area)
	drawX = int(x/g_dx)
#	print(elem, elemID, area, x)
	pixMap[drawX, pixel] = (255,255,255)
	#mark infinite element
	if len(elems[elem].positiveNeighbors) > 0:
		(neighID, unused) = elems[elem].positiveNeighbors[0]
		if neighID == 0:
			for x in range(drawX):
				pixMap[x, pixel] = (255,0,255)
			continue
	#mark walls
	if len(elems[elem].positiveNeighbors) == 0 or len(elems[elem].negativeNeighbors) == 0:
		for x in range(drawX):
			pixMap[x, pixel] = (255,255,255)
		continue
	#mark damped elems
	if elems[elem].damping != 0:
		for x in range(drawX):
			pixMap[x, pixel] = (0,127,0)

image.save(outfile)
hMappingFile.close()

print("fin.")
