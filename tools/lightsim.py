#!/usr/python3

import numpy
import sys
import os
import configparser
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

import elemfile
import infinitySection

g_bVerbose = sys.argv[1] == "1"
g_strSimuInputFile = sys.argv[2]


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

if g_bVerbose:
	print("lightsim: speakers:", dSpeakers)

g_fMaxTimeStep = float(config.get("general", "max_timestep"))
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

afInfinityDamping = [1.0] * len(aElems)

#element index 0 is the infinite element.
aPressureFactorsNeg = [0]
aPressureFactorsPos = [0]

# map for damped elements
afVelocityDamping = [0.0] * len(aElems)

# tuples of linked elements:
# (master, slave)
aPressureLinks = []

# list of pressure differences to delete
# just for tidiness, these elements are write-only
aUnusedPressureDifferences = [0]

for iElem in range(1, len(aElems)):
	#print("iElem", iElem)
	elem = aElems[iElem]
	
	# collect infinity elements
	afInfinityDamping[iElem] = elem.m_fSink
	
	# collect damping coefficients
	afVelocityDamping[iElem] = elem.m_fDamping

	fNegArea = aElems[iElem - 1].m_fArea
	fPosArea = elem.m_fArea
	
	# append volume to list
	fVolume = 0.5 * (fNegArea + fPosArea) * g_dx
	
	# this factor is missing time step and velocity factor
	fFactor = g_fDensity * g_fGasConstant * g_fTemperature/ fVolume
	
	# implement breaks on the left side of the element
	if elem.m_bBreak and iElem > 0:
		aPressureFactorsPos[-1] = 0
		fNegArea = 0

		aUnusedPressureDifferences.append(iElem - 1)
	
	aPressureFactorsNeg.append(fNegArea * fFactor)
	aPressureFactorsPos.append( -fPosArea * fFactor)
	
	# take care of links
	if elem.m_iLink != -1:
		if elem.m_fArea != aElems[elem.m_iLink].m_fArea:
			print("lightsim: ERROR linked element areas do not match!", iElem, elem.m_iLink)
		
		aPressureLinks.append( (elem.m_iLink, iElem) )

print("lightsim: number of elements:", len(aPressureFactorsNeg) - 1)

#pointing to velocity indices
for strSpeaker in dSpeakers:
	#route speaker velocity elem to correct pressure elem
	speaker = dSpeakers[strSpeaker]
	strSpeakerConfig = config.get("speakers", strSpeaker)
	
	speaker_config = configparser.ConfigParser()
	strSpeakerConfig = g_strDir + strSpeakerConfig
	if len(speaker_config.read(strSpeakerConfig) ) == 0:
		print("lightsim: ERROR reading speaker config", strSpeakerConfig)
	
	speaker.m_dOptions = dict()
	
	for opt in ["bl", "cms", "le", "mmd", "re", "rms", "sd"]:
		speaker.m_dOptions[opt] = float(speaker_config.get("tspset", opt))
	
	fRadius = numpy.sqrt(speaker.m_dOptions["sd"] / numpy.pi)
	speaker.m_fAirmass = (8.0/3.0) * g_fDensity * fRadius**3
	speaker.m_fStiffness = 1.0 / speaker.m_dOptions["cms"]
	
	# element cross section is given for right side (where the speaker is implemented)
	aPressureFactorsPos[speaker.m_iElemID]     *= speaker.m_dOptions["sd"] / aElems[speaker.m_iElemID].m_fArea
	aPressureFactorsNeg[speaker.m_iElemID + 1] *= speaker.m_dOptions["sd"] / aElems[speaker.m_iElemID].m_fArea

# time constraints
# speed of sound
lfTimeConstraints = [g_dx / numpy.sqrt(g_fGasConstant* g_fTemperature)]
# acoustic damping
lfTimeConstraints.append(g_fDensity / max(numpy.amax(afVelocityDamping), 1.0) )

'''
# iterate speakers
for strSpeaker in dSpeakers.keys():
	speaker = dSpeakers[strSpeaker]
	# speaker electric
	lfTimeConstraints.append(speaker.m_dOptions["le"] / speaker.m_dOptions["re"] )
	# mechanical damping speaker
	lfTimeConstraints.append(speaker.m_dOptions["mmd"] * speaker.m_dOptions["rms"] )
	# mechanical spring speaker
	lfTimeConstraints.append(numpy.sqrt(speaker.m_dOptions["mmd"] * speaker.m_dOptions["cms"]) )

'''
lfTimeConstraints.append(g_fMaxTimeStep)

g_fTimeStep = numpy.amin(lfTimeConstraints)

g_fVelocityFactor = g_fTimeStep / (g_fDensity * g_dx)

print("lightsim: using time step", g_fTimeStep, "s")

#print(aPressureFactorsNeg)
#print(aPressureFactorsPos)

#create pressure indexing vectors for simulation
npaPressureFactorsNeg = numpy.asarray(aPressureFactorsNeg) * g_fVelocityFactor * g_fTimeStep
npaPressureFactorsPos = numpy.asarray(aPressureFactorsPos) * g_fVelocityFactor * g_fTimeStep

npaDampingFactors = numpy.asarray(afVelocityDamping[1:]) * g_dx * g_fVelocityFactor

#list of infinity elements
npaInfinityDamping = numpy.asarray(afInfinityDamping)

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

if g_bVerbose:
	print("lightsim: pressure links", aPressureLinks)

#will be called with omega*t
def sinInput(omega_t):
	return numpy.sin(omega_t)

fSignalNormalizer = 4.0 # for 8 ohms
	
fnInput = sinInput

xmlTree = ET.ElementTree(ET.Element("simu_output") )
rootElem = xmlTree.getroot()

for strSpeaker in dSpeakers:
	if g_bVerbose:
		print("lightsim:", strSpeaker, ":")
		print("lightsim:", dSpeakers[strSpeaker].m_dOptions)

plt.clf()
fig, ax1 = plt.subplots()
ax2 = ax1.twinx()

#n = 50
n = 10000000

dlSPLs = dict()
dlImpedances = dict()

for speaker in dSpeakers.keys():
	dlImpedances[speaker] = []

for mic in dMics.keys():
	dlSPLs[mic] = []
	
dlSPLs["spl_sum"] = []

aafProfileSPLs = []

#lfPhase = []

# convergence settings for newton raphson speaker equation solver
nMaxIter = 5;
fEpsU = 1e-8;
fEpsF = 1e-8;
fEpsV = 1e-5;

#read parameters needed
for fFreq in g_afFreqs:
	if g_bVerbose:
		print("lightsim: frequency", fFreq)
	else:
		print('.', end="", flush=True)
	fSimulationDuration = g_fLeadTime + len(aElems) * g_dx / g_fSpeed  + 1.0 / fFreq * g_nSignalPeriods
	
	if g_bVerbose:
		print("lightsim: simulating period", fSimulationDuration, "s")
	
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
	
	npaSummedSquares = npaPressures

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
		
		npaPressures *= npaInfinityDamping
	
		#second half-step (basis are p-elements)
		#explicit integration for velocity elements
		npaPressureDifference = npaPressureDifference + (
			npaPressures[:-1] - npaPressures[1:]
			)
		
		# apply damping to the velocities (in the form of pressure differences)
		npaPressureDifference = npaPressureDifference - npaPressureDifference * npaDampingFactors
	
		# clear unused elements (just for tidiness)
		npaPressureDifference[aUnusedPressureDifferences] = 0
	
		#apply damping to "infinity" elements
		npaPressureDifference *= npaInfinityDamping[:-1]
		
		#invoke speaker input function
		fU = fnInput(2.0 * numpy.pi * fFreq * fTime) * fSignalNormalizer
		
		#print(numpy.argmax(npaPressureDifference))
		
		# process speakers
		for strSpeaker in dSpeakers:
			speaker = dSpeakers[strSpeaker]
			dOptions = speaker.m_dOptions

			fCurrent = speaker.m_fI			
			fPosition = speaker.m_fX
			fVelocity = speaker.m_fV
			
			fPressureDiff = npaPressures[speaker.m_iElemID + 1] - npaPressures[speaker.m_iElemID]
			
			fDeterminant = 1.0 / ((4*dOptions["re"]*g_fTimeStep+8*dOptions["le"])*(dOptions["mmd"] + speaker.m_fAirmass)+speaker.m_fStiffness*dOptions["re"]*g_fTimeStep*g_fTimeStep*g_fTimeStep+(2*dOptions["re"]*dOptions["rms"]+2*speaker.m_fStiffness*dOptions["le"]+2*dOptions["bl"]*dOptions["bl"])*g_fTimeStep*g_fTimeStep+4*dOptions["le"]*dOptions["rms"]*g_fTimeStep);
			
			for iIter in range(nMaxIter):
		
				fDeltaU = fU - dOptions["bl"] * (fVelocity + speaker.m_fV) / 2 - dOptions["re"] * (fCurrent + speaker.m_fI) / 2 - dOptions["le"] * (fCurrent - speaker.m_fI) / g_fTimeStep;
				fDeltaF = dOptions["bl"] * (fCurrent + speaker.m_fI) / 2 - dOptions["sd"] * fPressureDiff - speaker.m_fStiffness * (fPosition + speaker.m_fX) / 2 - dOptions["rms"] * (fVelocity - speaker.m_fV) / 2 - (dOptions["mmd"] + speaker.m_fAirmass) * (fVelocity - speaker.m_fV) / g_fTimeStep;
				fDeltaV = (fPosition - speaker.m_fX) / g_fTimeStep - (fVelocity + speaker.m_fV) / 2;

				# check for convergence
				if abs(fDeltaU) < fEpsU and abs(fDeltaF) < fEpsF and abs(fDeltaV) < fEpsV:
					break
		
				fCurrent = fCurrent + fDeterminant * (8*fDeltaU*g_fTimeStep*(dOptions["mmd"] + speaker.m_fAirmass)+(2*fDeltaU-2*dOptions["bl"]*fDeltaV)*speaker.m_fStiffness*g_fTimeStep*g_fTimeStep*g_fTimeStep+(4*fDeltaU*dOptions["rms"]-4*dOptions["bl"]*fDeltaF)*g_fTimeStep*g_fTimeStep);
				fPosition = fPosition + fDeterminant * -((4*fDeltaV*dOptions["re"]*g_fTimeStep*g_fTimeStep+8*fDeltaV*dOptions["le"]*g_fTimeStep)*(dOptions["mmd"] + speaker.m_fAirmass)+(2*fDeltaV*dOptions["re"]*dOptions["rms"]-2*fDeltaF*dOptions["re"]+2*dOptions["bl"]*dOptions["bl"]*fDeltaV-2*dOptions["bl"]*fDeltaU)*g_fTimeStep*g_fTimeStep*g_fTimeStep+(4*fDeltaV*dOptions["le"]*dOptions["rms"]-4*fDeltaF*dOptions["le"])*g_fTimeStep*g_fTimeStep);
				fVelocity = fVelocity + fDeterminant * (2*fDeltaV*speaker.m_fStiffness*dOptions["re"]*g_fTimeStep*g_fTimeStep*g_fTimeStep+(4*fDeltaF*dOptions["re"]+4*fDeltaV*speaker.m_fStiffness*dOptions["le"]+4*dOptions["bl"]*fDeltaU)*g_fTimeStep*g_fTimeStep+8*fDeltaF*dOptions["le"]*g_fTimeStep);

			if iIter >= nMaxIter:
				print("speaker equations failed to converge")
			
			speaker.m_fV = fVelocity
			speaker.m_fX = fPosition
			speaker.m_fI = fCurrent
			
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
			npaSummedSquares = npaSummedSquares + numpy.square(npaPressures)
				
		iStep += 1
		
		if iStep % n == 0:
			ax2.cla()
			ax1.cla()
			
			plt.suptitle("velocity and pressure")
			ax1.plot(g_fVelocityFactor * npaPressureDifference, "b-")
			ax1.set_ylabel('velocity', color='b')
			ax2.plot(npaPressures, "g-")
			ax2.set_ylabel('pressure', color='g')
			
			strPlotFile = str(iStep) + ".png"
			print("saving plot file", strPlotFile)
			
			plt.savefig(strPlotFile)
	
	def calcSPL(npaPressure):
		#calculate SPL
		fMicRMS = numpy.sqrt(numpy.sum(numpy.square(npaPressure) ) / npaPressure.size)
		return 20.0 * numpy.log10(fMicRMS/g_fReferencePressure);
	
	# virtual mic data for sum output
	npaSumPressure = []
	
	#save microphone measurements
	for strMic in dMics:
		# get pressure
		npaPressure = numpy.transpose(dMicMeasurements[strMic])[1]
		
		if "spl_mic" in strMic:
			if len(npaSumPressure) == 0:
				npaSumPressure = npaPressure
			else:
				npaSumPressure += npaPressure
		
		fPmax = numpy.amax(npaPressure)
		if g_bVerbose:
			print("pmax:", fPmax)
		
		fMicSPL = calcSPL(npaPressure)
		
		dlSPLs[strMic].append(fMicSPL)
		
		if g_bSaveTimeSeries:
			micElem = ET.SubElement(signalElem, "mic_output")
			micElem.attrib["id"] = strMic
			
			strFile = strMic + "_" + str(fFreq) + ".dat"
			micElem.attrib["file"] = strFile
			
			numpy.savetxt(g_strDir + strFile, dMicMeasurements[strMic] )
	
	# create a virtual mic capturing the sum output
	dlSPLs["spl_sum"].append( calcSPL(npaSumPressure) )
			
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
		
		if g_bVerbose:
			print("lightsim: xmax:", fXmax, "vmax:", fVmax)
		
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
	npaProfileAmplitudes = numpy.sqrt((npaSummedSquares + g_fReferencePressure * .01) * (1.0/len(npaSumPressure) ) )
	npaProfileSPL = 20.0 * numpy.log10(npaProfileAmplitudes /g_fReferencePressure )
	
	aafProfileSPLs.append(npaProfileSPL)

numpy.savetxt(g_strDir + "profiles.txt", aafProfileSPLs)
	
# save microphone SPL measurements
for mic in dlSPLs.keys():
	micElem = ET.SubElement(rootElem, "mic_spl")
	micElem.attrib["id"] = mic
	
	strFile = "spl_" + mic + ".dat"
	micElem.attrib["file"] = strFile
	
	numpy.savetxt(g_strDir + strFile, numpy.transpose([g_afFreqs, dlSPLs[mic]] ) )
	
# save speaker impedance
for speaker in dSpeakers.keys():
	micElem = ET.SubElement(rootElem, "speaker_impedance")
	micElem.attrib["id"] = speaker
	
	strFile = "impedance_speaker_" + speaker + ".dat"
	micElem.attrib["file"] = strFile
	
	numpy.savetxt(g_strDir + strFile, numpy.transpose([g_afFreqs, dlImpedances[speaker]]) )

if not g_bVerbose:
	print("")

print("lightsim: writing output XML to", g_strSimuOutputFile)

with open(g_strSimuOutputFile, 'wb') as f:
	f.write(bytes('<?xml version="1.0" encoding="UTF-8" ?>', 'utf-8'))
	xmlTree.write(f, 'utf-8')
