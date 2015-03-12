#!/usr/python3

from PIL import Image
import math
import sys

strOutputFile = sys.argv[1]
strGraphicsFile = sys.argv[2]
strImageBase = sys.argv[3]

#reads simulation output
#output = tab separated file
#<element id> <time> <pressure>

#parse sim output file
infile = open(strOutputFile, 'r')
dTimes = dict()

#find maximum pressure amplitude
fMaxAmpli = 0

for line in infile:
	fields = line.split('\t')

	elid = int(fields[0])
	time = float(fields[1])
	pres = float(fields[2])

	fMaxAmpli = max(fMaxAmpli, abs(pres))

	if not time in dTimes:
		dTimes[time] = dict()

	dTimes[time][elid] = pres

infile.close()

print("maximum amplitude", fMaxAmpli)

#reads element mapping
#mapping = tab separated file
#<element id> <x> <y> <max amplitude>
hMappingFile = open(strGraphicsFile + ".txt", 'r')
dElementMappings = dict()

for line in hMappingFile:
	fields = line.split('\t')
	dElementMappings[int(fields[0])] = (int(fields[1]), int(fields[2]), int(fields[3]) )

#reads element visualization
#just load image
im = Image.open(strGraphicsFile)

#writes images of pressure onto visualization
#normalize by max value

times = []
for a_time in dTimes.keys():
	times.append(a_time)

times.sort()

counter = 0

for time in times:
#	print("time:", time)
	imGraph = im.copy()
	pixMap = imGraph.load()

	dElements = dTimes[time]
	
	for element in dElements.keys():
		pressure = dElements[element]
		(posX, posY, posMaxX) = dElementMappings[element]
		posMaxX -= 1
		imageX = pressure / fMaxAmpli * posMaxX + posX
		imageY = posY
		
		pixMap[imageX, imageY] = (0,255,0)

	strCounter = str(counter)
	if len(strCounter) > 4:
		print("can't process more than 9999 images!")
		break

	while len(strCounter) < 4:
		strCounter = '0' + strCounter

	imGraph.save(strImageBase + strCounter + ".png")
	counter += 1

