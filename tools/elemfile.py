#!/usr/python3

#parse element input file

import math
import sys

class Elem:
	def __init__(self):
		self.m_fDamping = 0
		self.m_fArea = 0
		self.m_bBreak = False
		self.m_bGeom = True
		self.m_bSink = False
	
		# link syntax:
		#   -1: no link
		#   0: link to "infinity"
		#   >0: link to actual element
		self.m_iLink = -1
	
		# speaker will be inserted on the velocity link to the previous pressure element
		self.m_strSpeaker = ""
	
		# microphone definition. measures pressure of this pressure element
		self.m_strMic = ""
		
	
	def __str__(self):
		strDesc = "{element; area:" + str(self.m_fArea) + "; damping:" + str(self.m_fDamping)
		
		if self.m_strMic != "":
			strDesc += "; microphone \"" + self.m_strMic + "\""
		
		if self.m_strSpeaker != "":
			strDesc += "; speaker \"" + self.m_strSpeaker + "\""
		
		return strDesc + "}"

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
	aElems = []
	dMics = dict()
	dSpeakers = dict()

	f = open(strFilename, 'r')
	aLines = f.readlines()
	f.close()

#	delta X of the elements (length)
	dx = float("nan")

	iElem = -1

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
			aElems[-1].m_bBreak = True
		elif linetype == "l":
			iLinkTo = int(currLine[2:])
			aElems[-1].m_iLink = iLinkTo
		elif linetype == "s":
			speakerID = currLine[3:-2]
			
			aElems[-1].m_strSpeaker = speakerID
			spkr = Speaker()
			
			spkr.m_iElemID = iElem
			dSpeakers[speakerID] = spkr
		elif linetype == "m":
			micID = currLine[3:-2]
			
			mic = Microphone()
			mic.m_iElemID = iElem
			dMics[micID] = mic
			aElems[-1].m_strMic = micID
		elif linetype == "g":
			aElems[-1].m_bGeom = True
		elif linetype == "i":
			aElems[-1].m_bSink = True
			
		elif linetype == "x":
			dx = float(currLine[3:])
		elif linetype == "#":
			pass
		elif currLine == "\n":
			pass
		else:
			print("type of line not recognized!", currLine)
	return (aElems, dMics, dSpeakers, dx)

def writeElemFile(strFilename, aElements, fDx):
	strFileContents = "# set global element length\n"
	strFileContents += "x " + str(fDx) + "\n"
	
	strFileContents += "# define elements\n"
	
	for iElem in range(len(aElements)):
		strFileContents += "e " + str(iElem) + "\n"
		elem = aElements[iElem]
		
		strFileContents += "A " + str(elem.m_fArea) + "\n"
		
		if elem.m_fDamping != 0:
			strFileContents += "d " + str(elem.m_fDamping) + "\n"
		if elem.m_iLink != -1:
			strFileContents += "l " + str(elem.m_iLink) + "\n"
		if elem.m_bBreak:
			strFileContents += "b\n"
		if elem.m_bGeom:
			strFileContents += "g\n"
		if elem.m_bSink:
			strFileContents += "i\n"
		if elem.m_strSpeaker != "":
			strFileContents += "s \"" + elem.m_strSpeaker + "\"\n"
		if elem.m_strMic != "":
			strFileContents += "m \"" + elem.m_strMic + "\"\n"
		
	f = open(strFilename, 'w')
	f.write(strFileContents)
	f.close()
		

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

