#!/usr/python3

import numpy
import sys
import os
import configparser
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

import elemfile
import infinitySection

g_strSimuInputFile = sys.argv[1]

strOSDir = os.path.dirname(g_strSimuInputFile)

if strOSDir=="":
	strOSDir = "."

g_strDir = strOSDir + "/"

config = configparser.ConfigParser()

#read simulation input file
config.read(g_strSimuInputFile)
g_strSimuOutputFile = g_strDir + config.get("general", "output_file")
g_strElementFile = g_strDir + config.get("general", "element_file")

aElems, dMics, dSpeakers, g_dx = elemfile.scanElemFile(g_strElementFile)

print("speakers:", dSpeakers)

g_fMaxTimestep = float(config.get("general", "max_timestep"))
g_strSignalType = config.get("signal", "signal_type")

'''
		if(strSignal == std::string("sine"))
			data.m_SignalType = SIG_SINE;
		else if(strSignal == std::string("delta"))
			data.m_SignalType = SIG_DELTA;
		else if(strSignal == std::string("square"))
			data.m_SignalType = SIG_SQUARE;
'''

g_bSaveTimeSeries = False

g_strFreqs = config.get("signal", "frequencies")

g_afFreqs = []
for strFreq in g_strFreqs.split(";"):
	if strFreq == "":
		continue
	g_afFreqs.append(float(strFreq))

g_nSignalPeriods = int(config.get("signal", "signal_periods"))

#lead time including time-of-flight (has to be calculated by preceeding stage)
g_fLeadTime = float(config.get("signal", "lead_time"))

#read global configuration file (for constants)
#global_config = configparser.ConfigParser()
#global_config.read(g_strDir + g_strGlobalConfigFile)

# speed of sound [m/s]
g_fSpeed = 343.0
# density of air [kg/m3]
g_fDensity = 1.2041
# temperature of air [K]
g_fTemperature = 293.15
# gas constant of air [J/(kg K)]
g_fGasConstant = 287.0
# isentropic exponent [-]
g_fIsentropicExponent = 1.4
# reference pressure for 0 dB [Pa]
g_fReferencePressure = 0.00002
#g_ = config.get("constants", "speed")
#g_strElementFile = g_strDir + config.get("general", "element_file")

# infinity is a half space (infinite baffle)
g_fInfinitySpaceRatio = 0.5

# check for links to element 0, this will be the infinite element
g_nInfinteElements = 200
# meters of expansion prior to damped elements
g_fInfinityPreExpansion = 1.0
g_fInfinityTransition = 2.0

# damping factor for infinity
g_fInfiniteDampingFactor = 0.98

aInfiniteElementIndices = [0]

g_fTimeStep = 0.4 * g_dx/numpy.sqrt(g_fGasConstant* g_fTemperature)

g_fVelocityFactor = g_fTimeStep / (g_fDensity * g_dx)

print("using time step", g_fTimeStep, "s")

#element index 0 is the infinite element.
aPressureFactorsNeg = [0]
aPressureFactorsPos = [0]

# tuples of linked elements:
# (master, slave)
aPressureLinks = []

# list of pressure differences to delete
# just for tidiness, these elements are write-only
aUnusedPressureDifferences = [0]

for iElem in range(1, len(aElems)):
	#print("iElem", iElem)
	elem = aElems[iElem]
	
	fNegArea = aElems[iElem - 1].m_fArea
	fPosArea = elem.m_fArea
	
	# append volume to list
	fVolume = 0.5 * (fNegArea + fPosArea) * g_dx
	
	fFactor = g_fVelocityFactor * g_fDensity * g_fGasConstant * g_fTemperature * g_fTimeStep / fVolume
	
	aPressureFactorsNeg.append(fNegArea * fFactor)
	aPressureFactorsPos.append( -fPosArea * fFactor)
	
	# take care of links
	if elem.m_iLink == 0:
		print("infinity section from element", iElem)
	elif elem.m_iLink != -1:
		if elem.m_fArea != aElems[elem.m_iLink].m_fArea:
			print("ERROR: linked element areas do not match!", iElem, elem.m_iLink)
		
		aPressureLinks.append( (elem.m_iLink, iElem) )

for iElem in list(range(len(aElems)))[1:]:
	elem = aElems[iElem]
	
	# implement breaks
	if elem.m_bBreak:
		aPressureFactorsPos[iElem] = 0
		aPressureFactorsNeg[iElem + 1] = 0
		
		aUnusedPressureDifferences.append(iElem)

	# collect infinity elements
	if elem.m_iLink == 0:
		# create a link to end of element list
		iBaseElement = len(aPressureFactorsNeg)
		aPressureLinks.append( (iElem, iBaseElement) )
		
		# add pressure difference to unused ones
		aUnusedPressureDifferences.append(iBaseElement - 1)
		
		#create linked to element as a copy
		aPressureFactorsNeg.append(0)
		
		# this is the factor for constant cross section
		fFactor = g_fVelocityFactor * g_fDensity * g_fGasConstant * g_fTemperature * g_fTimeStep / g_dx
		aPressureFactorsPos.append(- fFactor)
		
		fLastArea = elem.m_fArea
			
		lfInfinityAreas = infinitySection.infinitySection(elem.m_fArea, g_fInfinitySpaceRatio, g_fInfinityPreExpansion, g_fInfinityTransition, g_dx)
		
		for iElement in range(len(lfInfinityAreas) + g_nInfinteElements - 1):
			# initialize with maximum
			fInfinityArea = lfInfinityAreas[-1]
				
			# if we are in the pre expansion, do not add a damping factor to these elements
			if iElement >= len(lfInfinityAreas):
				aInfiniteElementIndices.append(len(aPressureFactorsNeg) )
			else:
				fInfinityArea = lfInfinityAreas[iElement]
				
			fVolume = (fLastArea + fInfinityArea) * 0.5 * g_dx
			fLastArea = fInfinityArea
			fFactor = g_fVelocityFactor * g_fDensity * g_fGasConstant * g_fTemperature * g_fTimeStep / fVolume
			
			aPressureFactorsNeg.append(fLastArea * fFactor)
			aPressureFactorsPos.append( - fInfinityArea * fFactor)
			
		# arrest last factor to zero
		aPressureFactorsPos[-1] = 0			

print("number of elements:", len(aPressureFactorsNeg) - 1)

#pointing to velocity indices
for strSpeaker in dSpeakers:
	#route speaker velocity elem to correct pressure elem
	speaker = dSpeakers[strSpeaker]
	strSpeakerConfig = config.get("speakers", strSpeaker)
	
	speaker_config = configparser.ConfigParser()
	speaker_config.read(g_strDir + strSpeakerConfig)
	
	speaker.m_dOptions = dict()
	
	for opt in ["bl", "cms", "le", "mmd", "re", "rms", "sd"]:
		speaker.m_dOptions[opt] = float(speaker_config.get("tspset", opt))
	
	fRadius = numpy.sqrt(speaker.m_dOptions["sd"] / numpy.pi)
	speaker.m_fAirmass = (8.0/3.0) * g_fDensity * fRadius**3
	speaker.m_fStiffness = 1.0 / speaker.m_dOptions["cms"]
	
	# element cross section is given for right side (where the speaker is implemented)
	aPressureFactorsPos[speaker.m_iElemID]     *= speaker.m_dOptions["sd"] / aElems[speaker.m_iElemID].m_fArea
	aPressureFactorsNeg[speaker.m_iElemID + 1] *= speaker.m_dOptions["sd"] / aElems[speaker.m_iElemID].m_fArea

#print(aPressureFactorsNeg)
#print(aPressureFactorsPos)

#create pressure indexing vectors for simulation
npaPressureFactorsNeg = numpy.asarray(aPressureFactorsNeg)
npaPressureFactorsPos = numpy.asarray(aPressureFactorsPos)

#list of infinity elements
npaInfinityElementIndices = numpy.asarray(aInfiniteElementIndices)

def astext(a):
	strText = ""
	for s in a:
		strText += str(s) + "\t"
	return strText

'''
print("pressure element", astext(range(len(npaPressureFactorsNeg))))
print("1st indices", astext(npaPressureFactorsNeg))
print("1st factors", astext(npaPressureFactorsPos))

exit(0)
'''

print("pressure links", aPressureLinks)

#will be called with omega*t
def sinInput(omega_t):
	return numpy.sin(omega_t)

fSignalNormalizer = 4.0 # for 8 ohms
	
fnInput = sinInput

xmlTree = ET.ElementTree(ET.Element("simu_output") )
rootElem = xmlTree.getroot()

for strSpeaker in dSpeakers:
	print(strSpeaker, ":")
	print(dSpeakers[strSpeaker].m_dOptions)

plt.clf()
fig, ax1 = plt.subplots()
ax2 = ax1.twinx()

n = 50
n = 10000000

dlSPLs = dict()
dlImpedances = dict()

for speaker in dSpeakers.keys():
	dlImpedances[speaker] = []

for mic in dMics.keys():
	dlSPLs[mic] = []
	
#lfPhase = []

#read parameters needed
for fFreq in g_afFreqs:
	print("frequency:", fFreq)
	fSimulationDuration = g_fLeadTime + len(aElems) * g_dx / g_fSpeed  + 1.0 / fFreq * g_nSignalPeriods
	print("simulating period of", fSimulationDuration, "s")
	
	signalElem = ET.SubElement(rootElem, "signal")
	signalElem.attrib["freq"] = str(fFreq)
	signalElem.attrib["type"] = g_strSignalType

	#create vectors for simulation
	npaPressures = numpy.asarray([0] * len(aPressureFactorsNeg))
	npaPressureDifference = numpy.asarray([0] * (len(aPressureFactorsNeg)-1) )
	
	iStep = 0
	bBreak = False
	
	dMicMeasurements = dict()
	for strMic in dMics:
		dMicMeasurements[strMic] = []
		
	dSpeakerMeasurements = dict()
	for strSpeaker in dSpeakers:
		dSpeakerMeasurements[strSpeaker] = []
		speaker = dSpeakers[strSpeaker]
		
		speaker.m_fI = 0.0
		speaker.m_fX = 0.0
		speaker.m_fV = 0.0
		
	# array for linked elements
	afLinkedPressures = [0] * len(aPressureLinks)

	while(not bBreak):
		fTime = g_fTimeStep * iStep
		if fTime > fSimulationDuration:
			bBreak = True
		
		# first half-step (basis are v-elements)
	
		#explicit integration for pressure elements
		npaPressures = npaPressures + (
			npaPressureFactorsPos * numpy.append(npaPressureDifference, 0) +
			npaPressureFactorsNeg * numpy.append(0, npaPressureDifference)
			)
		
		# process linked elements
		
		# first iteration: collect slave pressures and apply to master
		for iPressureLink in range(len(aPressureLinks)):
			(iMaster, iSlave) = aPressureLinks[iPressureLink]
			npaPressures[iMaster] += npaPressures[iSlave] - afLinkedPressures[iPressureLink]
			
		# second iteration: distribute to slaves and update history
		for iPressureLink in range(len(aPressureLinks)):
			(iMaster, iSlave) = aPressureLinks[iPressureLink]
			npaPressures[iSlave] = npaPressures[iMaster] 
			
			afLinkedPressures[iPressureLink] = npaPressures[iMaster]
		
		npaPressures[npaInfinityElementIndices] *= g_fInfiniteDampingFactor
	
		#second half-step (basis are p-elements)
		#explicit integration for velocity elements
		npaPressureDifference = npaPressureDifference + (
			npaPressures[:-1] - npaPressures[1:]
			)
	
		# clear unused elements (just for tidiness)
		npaPressureDifference[aUnusedPressureDifferences] = 0
	
		#apply damping to "infinity" elements
		npaPressureDifference[npaInfinityElementIndices[:-1]] *= g_fInfiniteDampingFactor
		
		#invoke speaker input function
		fU = fnInput(2.0 * numpy.pi * fFreq * fTime) * fSignalNormalizer
		
		#print(numpy.argmax(npaPressureDifference))
		
		# process speakers
		for strSpeaker in dSpeakers:
			speaker = dSpeakers[strSpeaker]
			dOptions = speaker.m_dOptions
		
			#calculate current
			fCurrentSlope = (fU - dOptions["bl"]*speaker.m_fV - dOptions["re"] * speaker.m_fI)/dOptions["le"]
			speaker.m_fI = speaker.m_fI + fCurrentSlope * g_fTimeStep
			
			fForceMembrane = dOptions["bl"] * speaker.m_fI
			fPressureDiff = npaPressures[speaker.m_iElemID + 1] - npaPressures[speaker.m_iElemID]
			
			#calculate speaker acceleration
			fAcceleration = (fForceMembrane - fPressureDiff * dOptions["sd"] - speaker.m_fX * speaker.m_fStiffness - dOptions["rms"] * speaker.m_fV)/(dOptions["mmd"] + speaker.m_fAirmass)

			#calculate speaker velocity			
			speaker.m_fV = speaker.m_fV + fAcceleration * g_fTimeStep
			
			#calculate speaker position
			speaker.m_fX = speaker.m_fX + speaker.m_fV * g_fTimeStep
			
			#overwrite updates made by pressure step
			npaPressureDifference[speaker.m_iElemID] = speaker.m_fV / g_fVelocityFactor
			
			if fTime > g_fLeadTime:
				#save speaker measurements			
				dSpeakerMeasurements[strSpeaker].append([fTime, fU, speaker.m_fI, speaker.m_fV, speaker.m_fX])

		if fTime > g_fLeadTime:
			#save microphone measurements
			for strMic in dMics:
				iElem = dMics[strMic].m_iElemID
				dMicMeasurements[strMic].append([fTime, npaPressures[iElem]])
			
			#save element measurements
				
		iStep += 1
		
		if iStep % n == 0:
			ax2.cla()
			ax1.cla()
			
			plt.suptitle("velocity")
			ax1.plot(g_fVelocityFactor * npaPressureDifference, "b-")
			ax1.set_ylabel('velocity', color='b')
			ax2.plot(npaPressures, "g-")
			ax2.set_ylabel('pressure', color='g')
			
			plt.savefig(str(iStep) + ".png")
	
	#save microphone measurements
	for strMic in dMics:
		# get pressure
		npaPressure = numpy.transpose(dMicMeasurements[strMic])[1]
		
		fPmax = numpy.amax(npaPressure)
		print("pmax:", fPmax)
		
		#calculate SPL
		fMicRMS = numpy.sqrt(numpy.sum(numpy.square(npaPressure) ) / npaPressure.size)
		fMicSPL = 20.0 * numpy.log10(fMicRMS/g_fReferencePressure);
		
		dlSPLs[strMic].append(fMicSPL)
		
		if g_bSaveTimeSeries:
			micElem = ET.SubElement(signalElem, "mic_output")
			micElem.attrib["id"] = strMic
			
			strFile = strMic + "_" + str(fFreq) + ".dat"
			micElem.attrib["file"] = strFile
			
			numpy.savetxt(g_strDir + strFile, dMicMeasurements[strMic] )
			
	#save speaker measurements
	for strSpeaker in dSpeakers:
		# get voltage and current
		npaVoltage = numpy.transpose(dSpeakerMeasurements[strSpeaker])[1]
		npaCurrent = numpy.transpose(dSpeakerMeasurements[strSpeaker])[2]
		
		# calculate RMS current
		fRMSVoltage = numpy.sqrt(numpy.sum(numpy.square(npaVoltage) ) / npaVoltage.size)
		fRMSCurrent = numpy.sqrt(numpy.sum(numpy.square(npaCurrent) ) / npaCurrent.size)
		
		dlImpedances[strSpeaker].append(fRMSVoltage / fRMSCurrent)
		
		# calculate x_max
		npaV = numpy.transpose(dSpeakerMeasurements[strSpeaker])[3]
		fVmax = numpy.amax(npaV)
		
		npaX = numpy.transpose(dSpeakerMeasurements[strSpeaker])[4]
		fXmax = numpy.amax(npaX)
		
		print("xmax:", fXmax, "vmax:", fVmax)
		
		if g_bSaveTimeSeries:
			speakerElem = ET.SubElement(signalElem, "speaker_output")
			speakerElem.attrib["id"] = strSpeaker
			
			strFile = strSpeaker + "_" + str(fFreq) + ".dat"
			speakerElem.attrib["file"] = strFile
			
			numpy.savetxt(g_strDir + strFile, dSpeakerMeasurements[strSpeaker] )
	
'''
	#save element measurements
	signalElem = ET.SubElement(signalElem, "element_output")
	signalElem.attrib["file"] = g_strPath +
'''
			
# save microphone SPL measurements
for mic in dMics.keys():
	micElem = ET.SubElement(rootElem, "mic_spl")
	micElem.attrib["id"] = strMic
	
	strFile = "spl_mic_" + mic + ".dat"
	micElem.attrib["file"] = strFile
	
	numpy.savetxt(g_strDir + strFile, numpy.transpose([g_afFreqs, dlSPLs[mic]] ) )
	
# save speaker impedance
for speaker in dSpeakers.keys():
	micElem = ET.SubElement(rootElem, "speaker_impedance")
	micElem.attrib["id"] = speaker
	
	strFile = "impedance_speaker_" + speaker + ".dat"
	micElem.attrib["file"] = strFile
	
	numpy.savetxt(g_strDir + strFile, numpy.transpose([g_afFreqs, dlImpedances[speaker]]) )
			
print("writing output XML to", g_strSimuOutputFile)

with open(g_strSimuOutputFile, 'wb') as f:
	f.write(bytes('<?xml version="1.0" encoding="UTF-8" ?>', 'utf-8'))
	xmlTree.write(f, 'utf-8')
