#!/usr/python3

#parse element input file

import math
import sys

#

class Elem:
	negativeNeighbors = []; #tuple: id, area
	positiveNeighbors = [];
	damping = 0;
	def __str__(self):
		return "{element; neg:" + str(self.negativeNeighbors) + "; pos:" + str(self.positiveNeighbors) + "; damp:" + str(self.damping) + "}"

class Microphone:
	m_iElemID = 0
	def __str__(self):
		return "{microphone; element:" + str(self.m_iElemID) + "}"

class Speaker:
	positiveElem = -1;
	negativeElem = -1;
	def __str__(self):
		return "{speaker; neg:" + str(self.negativeElem) + "; pos:" + str(self.positiveElem) + "}"

# returns dictionaries of objects
# return (dElems, dMics, dSpeakers, dx)

def scanElemFile(strFilename):
	dElems = dict()
	dMics = dict()
	dSpeakers = dict()

	f = open(strFilename, 'r')
	aLines = f.readlines()
	f.close()

#	delta X of the elements (length)
	dx = float("nan")

	def scanAttribs(aLines, iLine):
		negativeNeighbors = []
		positiveNeighbors = []
		damping = 0

		bLineForElem = True
		while(iLine < len(aLines)):
			currLine = aLines[iLine]
			attribType = currLine[0]
#			print("attribute type is", attribType)
			if attribType == "-":
				substrings = currLine.split(" ")
#				print("substrings are:", substrings)
				conn = int(substrings[1])
				area = float(substrings[2])
				negativeNeighbors.append( (conn, area) )
			elif attribType == "+":
				substrings = currLine.split(" ")
#				print("substrings are:", substrings)
				conn = int(substrings[1])
				area = float(substrings[2])
				positiveNeighbors.append( (conn, area) )
			elif attribType == "d":
				damping = float(currLine[2:])
			elif attribType == "#":
				pass
			else:
				break
			iLine += 1
		return (negativeNeighbors, positiveNeighbors, damping, iLine -1)

	iLine = 0

	while iLine < len(aLines):
		currLine = aLines[iLine]
		linetype = currLine[0]

#		print ("type of line", iLine, "is", linetype)

		if linetype == "e":
			elID = int(currLine[2:])
#			print("element ID is", elID)
			(negN, posN, damp, line) = scanAttribs(aLines, iLine + 1)

			elem = Elem()
			elem.negativeNeighbors = negN
			elem.positiveNeighbors = posN
			elem.damping = damp
			dElems[elID] = elem
			iLine = line
		elif linetype == "s":
#			print("speaker!")
			speakerID = currLine[3:-2]
			(negN, posN, damp, line) = scanAttribs(aLines, iLine + 1)

			spkr = Speaker()
			(spkr.positiveElem, unused) = posN[0]
			(spkr.negativeElem, unused) = negN[0]
#			spkr.positiveElem = posN[0]
#			spkr.negativeElem = negN[0]

			dSpeakers[speakerID] = spkr
			iLine = line
		elif linetype == "m":
			astrTemp = currLine.split(" ")
			micElem = int(astrTemp[-1])
			micID = astrTemp[-2][1:-1]
			
			elem = Microphone()
			elem.m_iElemID = micElem
			dMics[micID] = elem
			
#			print("mic ID", micID)
		elif linetype == "d":
			#HACK: this is the 'dx' element
			dx = float(currLine[3:])
#			print("element length is", dx)
		elif linetype == "#":
			pass
		elif currLine == "\n":
			pass
		else:
			print("type of line not recognized!", currLine)
		iLine += 1
	return (dElems, dMics, dSpeakers, dx)

if __name__ == "__main__":
	infile = sys.argv[1]
	dElems, dMics, dSpeakers, dx = scanElemFile(infile)

	for elem in dElems.keys():
		print("elem", elem, dElems[elem])
	
	for mic in dMics.keys():
		print("mic", mic, dMics[mic])

	for speaker in dSpeakers.keys():
		print("speaker", speaker, dSpeakers[speaker])

	print("dx", dx)

