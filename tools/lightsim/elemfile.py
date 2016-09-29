#!/usr/python3

#parse element input file

import math
import sys

class Elem:
	m_fDamping = 0;
	m_fArea = 0;
	m_bBreakConnection = False;
	m_iLink = -1;
	def __str__(self):
		return "{element; area:" + str(self.m_fArea) + "; damping:" + str(self.m_fDamping) + "}"

class Microphone:
	m_iElemID = 0
	def __str__(self):
		return "{microphone; element:" + str(self.m_iElemID) + "}"

class Speaker:
	m_iElemID = 0
	def __str__(self):
		return "{speaker; element:" + str(self.m_iElemID) + "}"

# returns dictionaries of objects
# return (dElems, dMics, dSpeakers, dx)

def scanElemFile(strFilename):
	aElems = [None]
	dMics = dict()
	dSpeakers = dict()

	f = open(strFilename, 'r')
	aLines = f.readlines()
	f.close()

#	delta X of the elements (length)
	dx = float("nan")

	iElem = 0
	
	elem = None

	for currLine in aLines:
		linetype = currLine[0]

#		print ("type of line", iLine, "is", linetype)

		if linetype == "e":
			iElem += 1
			elID = int(currLine[2:])
			
			if iElem != elID:
					print("ERROR: expected element ID to be", iElem, "not", elID)
#			print("element ID is", elID)
			elem = Elem()
			aElems.append( elem )
		elif linetype == "d":
			fDamping = float(currLine[2:])
			aElems[-1].m_fDamping = fDamping
		elif linetype == "A":
			fArea = float(currLine[2:])
			aElems[-1].m_fArea = fArea
		elif linetype == "b":	
			aElems[-1].m_bBreakConnection = True
		elif linetype == "l":
			iLinkTo = int(currLine[2:])
			aElems[-1].m_iLink = iLinkTo
		elif linetype == "s":
#			print("speaker!")
			speakerID = currLine[3:-2]
			spkr = Speaker()
			
			spkr.m_iElemID = iElem
			dSpeakers[speakerID] = spkr
		elif linetype == "m":
			micID = currLine[3:-2]
			
			mic = Microphone()
			mic.m_iElemID = iElem
			dMics[micID] = mic
			
#			print("mic ID", micID)
		elif linetype == "x":
			dx = float(currLine[3:])
#			print("element length is", dx)
		elif linetype == "#":
			pass
		elif currLine == "\n":
			pass
		else:
			print("type of line not recognized!", currLine)
	return (aElems, dMics, dSpeakers, dx)

if __name__ == "__main__":
	infile = sys.argv[1]
	dElems, dMics, dSpeakers, dx = scanElemFile(infile)

	for elem in aElems:
		print("elem", elem, dElems[elem])
	
	for mic in dMics.keys():
		print("mic", mic, dMics[mic])

	for speaker in dSpeakers.keys():
		print("speaker", speaker, dSpeakers[speaker])

	print("dx", dx)

