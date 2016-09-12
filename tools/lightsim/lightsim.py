#!/usr/python3cu

import numpy
import sys
import os
import configparser
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

import elemfile

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

dElems, dMics, dSpeakers, g_dx = elemfile.scanElemFile(g_strElementFile)

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

# get max element ID
aIDs = []

#look for links to element 0, this will be the infinite element
g_nInfinteElements = 100
g_fInfiniteDampingFactor = 0.96 # 0.95

aInfinitePressureIndices = []
aInfiniteVelocityIndices = []

#factors will first be filled with areas
aVelocity1stIndices = []
aVelocity1stFactors = []
aVelocity1stAreas   = []
aVelocity2ndIndices = []
aVelocity2ndFactors = []
aVelocity2ndAreas   = []

# [id] -> set(id1, id2, ...)
dConnections = dict()
dVolumes = dict()

g_fTimeStep = 0.2 * g_dx/numpy.sqrt(g_fGasConstant* g_fTemperature)

print("using time step", g_fTimeStep, "s")

for iID in dElems.keys():
	aIDs.append(iID)
	
nPressureElems = numpy.max(aIDs) + 1

nInfinityElems = 0

for iID in dElems.keys():
	neighbors = []
	fTotalArea = 0
	
	for neighborList, sign in [(dElems[iID].positiveNeighbors, 1), (dElems[iID].negativeNeighbors, -1)]:
		for target, area in neighborList:
			neighbors.append( (target, area, sign) )
			fTotalArea += area
	
	#check whether just one neighbor
	for neighborList in [dElems[iID].positiveNeighbors, dElems[iID].negativeNeighbors]:
		if len(neighborList) == 0:
			fTotalArea *= 2.0
	
	fVolume = fTotalArea * 0.5 * g_dx
	dVolumes[iID] = fVolume
	#print("pressure elem", iID, "volume", fVolume)
	
	aVelocityElements = []
	
	for target, area, sign in neighbors:
		if iID in dConnections:
			if target in dConnections[iID]:
				#this connection has already been processed
				continue
		else:
			dConnections[iID] = set()
		if not target in dConnections:
			dConnections[target] = set()
	
		fFactor = g_fTimeStep / (g_fDensity * fVolume)

		bCreateInfinity = False

		if target == 0:
			#redirect target to newly created element
			target = nPressureElems
			bCreateInfinity = True
		else:
			#add connection to list of implemented ones
			dConnections[target].add(iID)

		#print("velocity element", len(aVelocity1stIndices),":", iID, "->", target, "area", area)

		aVelocity1stIndices.append(iID)
		aVelocity1stFactors.append(area * fFactor)
		aVelocity1stAreas.append(area)
		
		aVelocity2ndIndices.append(target)
		aVelocity2ndFactors.append(- area * fFactor)
		aVelocity2ndAreas.append(area)
		
		dConnections[iID].add(target)
		
		if bCreateInfinity:
			aInfinitePressureIndices.append(target)
			dVolumes[target] = fVolume
			
			# infinity is a half space (infinite baffle)
			fInfinitySpaceRatio = 0.5
			
			fRadius0 = numpy.sqrt(area / (4*numpy.pi*fInfinitySpaceRatio))
			fLastArea = area
			
			for iElement in range(g_nInfinteElements - 1):
				iInfiniteElem = target + iElement + 1
				aInfinitePressureIndices.append(iInfiniteElem)
				aInfiniteVelocityIndices.append(len(aVelocity1stIndices))
				
				aVelocity1stIndices.append(iInfiniteElem - 1)
				aVelocity1stFactors.append(fFactor * fLastArea)
				aVelocity1stAreas.append(fLastArea)
				
				fSphereRadius = fRadius0 + iElement * g_dx
				fSphereArea = fInfinitySpaceRatio * 4 * numpy.pi * fSphereRadius ** 2
				
				dVolumes[iInfiniteElem] = (fLastArea + fSphereArea) * 0.5 * g_dx
		
				fLastArea = fSphereArea
				
				aVelocity2ndIndices.append(iInfiniteElem)
				aVelocity2ndFactors.append(- fFactor * fLastArea)
				aVelocity2ndAreas.append(fLastArea)
				
			nPressureElems += g_nInfinteElements
		
print("volumes", dVolumes)
#exit(0)		

nVelocityElems = len(aVelocity1stIndices)

print("number of elements:", nPressureElems - 1)

#element index 0 is the infinite element.
aPressure1stIndices = [-1] * nPressureElems
aPressure1stFactors = [0.0] * nPressureElems
aPressure2ndIndices = [-1] * nPressureElems
aPressure2ndFactors = [0.0] * nPressureElems
aPressure3rdIndices = [-1] * nPressureElems
aPressure3rdFactors = [0.0] * nPressureElems

aVolumes = [0] * nPressureElems
for iID in dVolumes:
	aVolumes[iID] = dVolumes[iID]

#iterate velocity elements to fill pressure factors
for index in range(len(aVelocity1stIndices)):
	aConnections =  [(aVelocity1stIndices[index], aVelocity1stAreas[index], -1), (aVelocity2ndIndices[index], aVelocity2ndAreas[index], 1)]
	
	for (iID, area, sign) in aConnections:
		fVolume = aVolumes[iID]
		#print("pressure elem", iID, "-> velocity elem", index, "area", area, "volume", fVolume)
		fFactor = sign * area * g_fDensity * g_fGasConstant * g_fTemperature * g_fTimeStep / fVolume

		if aPressure1stIndices[iID] == -1:
			aPressure1stIndices[iID] = index
			aPressure1stFactors[iID] = fFactor
		elif aPressure2ndIndices[iID] == -1:
			aPressure2ndIndices[iID] = index
			aPressure2ndFactors[iID] = fFactor
		elif aPressure3rdIndices[iID] == -1:
			print("setting 3rd connection to element", iID, "connecting to velocity elem", index)
			aPressure3rdIndices[iID] = index
			aPressure3rdFactors[iID] = fFactor
		else:
			print("ERROR: more than three connections for element", iID)

'''
print(aPressure1stIndices)
print(aPressure2ndIndices)
print(aPressure3rdIndices)
'''

#each element is a pressure element
#each link between the elements is a velocity element

nTotalVelocityElems = nVelocityElems
#create speaker elements as fake velocity elements
nSpeakers = len(dSpeakers)
nTotalVelocityElems += nSpeakers

for arr in [aVelocity1stFactors, aVelocity1stIndices, aVelocity2ndFactors, aVelocity2ndIndices]:
	arr += [0] * nSpeakers

#pointing to velocity indices
aSpeakerIndices = list(range(nVelocityElems, nTotalVelocityElems))
iSpeakerIndex = nVelocityElems
for strSpeaker in dSpeakers:
	#route speaker velocity elem to correct pressure elem
	speaker = dSpeakers[strSpeaker]
	strSpeakerConfig = config.get("speakers", strSpeaker)
	
	speaker_config = configparser.ConfigParser()
	speaker_config.read(g_strDir + strSpeakerConfig)
	
	speaker.m_dOptions = dict()
	
	speaker.m_iVelocityIndex = iSpeakerIndex
	
	for opt in ["bl", "cms", "le", "mmd", "re", "rms", "sd"]:
		speaker.m_dOptions[opt] = float(speaker_config.get("tspset", opt))
	
	fRadius = numpy.sqrt(speaker.m_dOptions["sd"] / numpy.pi)
	speaker.m_fAirmass = (8.0/3.0) * g_fDensity * fRadius**3
	speaker.m_fStiffness = 1.0 / speaker.m_dOptions["cms"]
	
	for elem, sign in [(speaker.negativeElem, -1), (speaker.positiveElem, 1)]:
		#assert that element doen't have a false connection there
		if aPressure2ndIndices[elem] != -1:
			print("error implanting speaker: element", elem, "already has connection")

		#implant speaker
		print("implanting speaker: element", elem, "to speaker index", iSpeakerIndex)
		aPressure2ndIndices[elem] = iSpeakerIndex
		#calculate factor to match membrane area, no matter what size the actual element is
		fVolume = aVolumes[elem]
		fFactor = speaker.m_dOptions["sd"] * g_fDensity * g_fGasConstant * g_fTemperature * g_fTimeStep / fVolume
		aPressure2ndFactors[elem] = sign * fFactor
	
	iSpeakerIndex += 1
	
#create pressure indexing vectors for simulation
npaPressure1stIndices = numpy.asarray(aPressure1stIndices)
npaPressure1stFactors = numpy.asarray(aPressure1stFactors)
npaPressure2ndIndices = numpy.asarray(aPressure2ndIndices)
npaPressure2ndFactors = numpy.asarray(aPressure2ndFactors)
npaPressure3rdIndices = numpy.asarray(aPressure3rdIndices)
npaPressure3rdFactors = numpy.asarray(aPressure3rdFactors)

#create velocity vectors for simulation
npaVelocity1stIndices = numpy.asarray(aVelocity1stIndices)
npaVelocity1stFactors = numpy.asarray(aVelocity1stFactors)
npaVelocity2ndIndices = numpy.asarray(aVelocity2ndIndices)
npaVelocity2ndFactors = numpy.asarray(aVelocity2ndFactors)

#list of infinity elements
npaPressureInfinityIndices = numpy.asarray(aInfinitePressureIndices)
npaVelocityInfinityIndices = numpy.asarray(aInfiniteVelocityIndices)

npaSpeakerIndices = numpy.asarray(aSpeakerIndices)

def astext(a):
	strText = ""
	for s in a:
		strText += str(s) + "\t"
	return strText

'''
print("pressure element", astext(range(len(npaPressure1stIndices))))
print("1st indices", astext(npaPressure1stIndices))
print("1st factors", astext(npaPressure1stFactors))
print("2nd indices", astext(npaPressure2ndIndices))
print("2nd factors", astext(npaPressure2ndFactors))
print("3rd indices", astext(npaPressure3rdIndices))
print("3rd factors", astext(npaPressure3rdFactors))

print()
print("velocity element", astext(range(len(npaVelocity1stIndices))))
print("1st indices", astext(npaVelocity1stIndices))
print("1st factors", astext(npaVelocity1stFactors))
print("2nd indices", astext(npaVelocity2ndIndices))
print("2nd factors", astext(npaVelocity2ndFactors))

exit(0)
'''

#will be called with omega*t
def sinInput(t):
	return numpy.sin(t)

fSignalNormalizer = 4.0 # for 8 ohms
	
fnInput = sinInput

xmlTree = ET.ElementTree(ET.Element("simu_output") )
rootElem = xmlTree.getroot()

#rootElem.attrib["id"] = config["Chassis"]["manufactor"] + " " + config["Chassis"]["name"]

#valueElem = ET.SubElement(rootElem, key)
#valueElem.text = str(dReadValues[key])
for strSpeaker in dSpeakers:
	print(strSpeaker, ":")
	print(dSpeakers[strSpeaker].m_dOptions)


plt.clf()
fig, ax1 = plt.subplots()
ax2 = ax1.twinx()

n = 1000000

dlSPLs = dict()
dlImpedances = dict()

for speaker in dSpeakers.keys():
	dlImpedances[speaker] = []

for mic in dMics.keys():
	dlSPLs[mic] = []
	
#lfPhase = []

#read parameters needed
for fFreq in g_afFreqs:
	print(fFreq)
	fSimulationDuration = g_fLeadTime + 1.0 / fFreq * g_nSignalPeriods
	print("simulating period of", fSimulationDuration, "s")
	
	signalElem = ET.SubElement(rootElem, "signal")
	signalElem.attrib["freq"] = str(fFreq)
	signalElem.attrib["type"] = g_strSignalType

	#create vectors for simulation
	npaPressures = numpy.asarray([0] * nPressureElems)
	npaVelocities = numpy.asarray([0] * nTotalVelocityElems)
	
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

		
	while(not bBreak):
		fTime = g_fTimeStep * iStep
		if fTime > fSimulationDuration:
			bBreak = True
		
		# first half-step (basis are v-elements)
	
		#print(npaPressures)
		#explicit integration for pressure elements
		npaPressures = npaPressures + npaPressure1stFactors * npaVelocities[npaPressure1stIndices] + npaPressure2ndFactors * npaVelocities[npaPressure2ndIndices] + npaPressure3rdFactors * npaVelocities[npaPressure3rdIndices]
		#print(npaPressures)
		
		npaPressures[npaPressureInfinityIndices] *= g_fInfiniteDampingFactor
	
		#second half-step (basis are p-elements)
		#explicit integration for velocity elements
		npaVelocities = npaVelocities + npaVelocity1stFactors * npaPressures[npaVelocity1stIndices] + npaVelocity2ndFactors * npaPressures[npaVelocity2ndIndices]
	
		#apply damping to "infinity" elements
		npaVelocities[npaVelocityInfinityIndices] *= g_fInfiniteDampingFactor
		
		#invoke speaker input function
		fU = fnInput(2.0 * numpy.pi * fFreq * fTime) * fSignalNormalizer
		
		# process speakers
		for strSpeaker in dSpeakers:
			speaker = dSpeakers[strSpeaker]
			dOptions = speaker.m_dOptions
		
			#calculate current
			fCurrentSlope = (fU - dOptions["bl"]*speaker.m_fV - dOptions["re"] * speaker.m_fI)/dOptions["le"]
			speaker.m_fI = speaker.m_fI + fCurrentSlope * g_fTimeStep
			
			fForceMembrane = dOptions["bl"] * speaker.m_fI
			fPressureDiff = npaPressures[speaker.positiveElem] - npaPressures[speaker.negativeElem]
			
			#calculate speaker acceleration
			fAcceleration = (fForceMembrane - fPressureDiff * dOptions["sd"] - speaker.m_fX * speaker.m_fStiffness - dOptions["rms"] * speaker.m_fV)/(dOptions["mmd"] + speaker.m_fAirmass)

			#calculate speaker velocity			
			speaker.m_fV = speaker.m_fV + fAcceleration * g_fTimeStep
			
			#calculate speaker position
			speaker.m_fX = speaker.m_fX + speaker.m_fV * g_fTimeStep
			
			#overwrite updates made by pressure step
			npaVelocities[speaker.m_iVelocityIndex] = speaker.m_fV
			
			#print(npaVelocities[speaker.m_iVelocityIndex])
			
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
			ax1.plot(npaVelocities, "b-")
			ax1.set_ylabel('velocity', color='b')
			ax2.plot(npaPressures, "g-")
			ax2.set_ylabel('pressure', color='g')
			
			plt.savefig(str(iStep) + ".png")
			#print(iStep)
	
	#save microphone measurements
	for strMic in dMics:
		# get pressure
		npaPressure = numpy.transpose(dMicMeasurements[strMic])[1]
		
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

