#!/usr/python3

#track chains of elements in the input file and draw a pretty image

import numpy
import sys
import os
import configparser

#xml support
import xml.etree.ElementTree as ET

#call external program
from subprocess import call

import material_costs

g_strSimuInputFile = sys.argv[1]
g_lstrSimuCommand = sys.argv[2:]

strOSDir = os.path.dirname(g_strSimuInputFile)

if strOSDir=="":
	strOSDir = "."

g_strDir = strOSDir + "/"

print("run directory", g_strDir)

print("calling", g_lstrSimuCommand, "with", g_strSimuInputFile, "in", g_strDir)
#call simulation with all the data
call(g_lstrSimuCommand + [g_strSimuInputFile], cwd=g_strDir)

#find out where the output went
config = configparser.ConfigParser()

config.read(g_strSimuInputFile)
g_strSimuOutputFile = g_strDir + config.get("general", "output_file")
g_strElementFile = g_strDir + config.get("general", "element_file")

#collect results
#parse simu output file
tree = ET.parse(g_strSimuOutputFile)
root = tree.getroot()
daMicSPLs = dict()
daSpeakerImpedances = dict()
#periods for measuring spl and phase
g_nMeasPeriods = 3
#process signals
for signal in root.findall("signal"):
	strSignalType = signal.attrib["type"]
	fSsignalFreq = float(signal.attrib["freq"])
	print("Signal - type =", strSignalType, ", freq =", fSsignalFreq)
	#process outputs
	for mic_output in signal.findall("mic_output"):
		strMicId = mic_output.attrib["id"]
		strMicFile = mic_output.attrib["file"]
		print("Mic - id =", strMicId, ", file =", strMicFile)
		#load output file
		npaMicOutput = numpy.loadtxt(g_strDir + strMicFile);
		
		npaPressures = numpy.transpose(npaMicOutput)[1]
		
		fMicRMS = numpy.sqrt(numpy.sum(numpy.square(npaPressures) ) / npaPressures.size)
		
		fMicSPL = 20*numpy.log10(fMicRMS/2.0e-5);
		if not strMicId in daMicSPLs:
			daMicSPLs[strMicId] = []
		daMicSPLs[strMicId].append( [fSsignalFreq, fMicSPL] )
	
	for speaker_output in signal.findall("speaker_output"):
		strSpeakerId = speaker_output.attrib["id"]
		strSpeakerFile = speaker_output.attrib["file"]
		print("Speaker - id =", strSpeakerId, ", file =", strSpeakerFile)
		#load output file
		npaSpeakerOutput = numpy.loadtxt(g_strDir + strSpeakerFile);
		
		npaVoltage = numpy.transpose(npaSpeakerOutput)[1]
		fVoltageRMS = numpy.sqrt(numpy.sum(numpy.square(npaVoltage) ) / npaVoltage.size)
		
		npaCurrent = numpy.transpose(npaSpeakerOutput)[2]
		fCurrentRMS = numpy.sqrt(numpy.sum(numpy.square(npaCurrent) ) / npaCurrent.size)
		
		fImpedance = fVoltageRMS / fCurrentRMS
		
		if not strSpeakerId in daSpeakerImpedances:
			daSpeakerImpedances[strSpeakerId] = []
		daSpeakerImpedances[strSpeakerId].append( [fSsignalFreq, fImpedance] )
	#video output is per frequency, no iteration needed.
	
#write spl files for mics
for strMicID in daMicSPLs:
	numpy.savetxt(g_strDir + "spl_mic_" + strMicID + ".txt", daMicSPLs[strMicID])

#write impedance files for speakers
for strSpeakerId in daSpeakerImpedances:
	numpy.savetxt(g_strDir + "impedance_speaker_" + strSpeakerId + ".txt", daSpeakerImpedances[strSpeakerId] )

#calculate costs for this design
dMatCosts = material_costs.get_material_costs(g_strElementFile)

#specific cost for missing one decade
k_spec_decade = 2000
#specific cost for spl deviation
k_spec_spl = 90

#optimization targets
t_spl = 110
t_edge_low = 20
t_edge_high = 400


t_mic = None

for mic in daMicSPLs.keys():
	if "Space" in mic:
		t_mic = mic

#calculate cost for a linear response fit
def linearResponseCost(npaSPL, fSPL, fLowEdge, fHighEdge):
	#edge cost is easy
	k_high = numpy.log10(t_edge_high / fHighEdge) * k_spec_decade
	k_low = numpy.log10(t_edge_low / fLowEdge) * k_spec_decade

	k_high = max(0, k_high)
	k_low = max(0, k_low)
	
	#check linearity
	npaTransposed = numpy.transpose(npaSPL)
	npaFreqs = npaTransposed[0]
	npaSPLs = npaTransposed[1]
	
	npaFreqMask = (npaFreqs > fLowEdge) * (npaFreqs < fHighEdge)
	
	npaTestSPLs = npaSPLs[numpy.flatnonzero(npaFreqMask)]
	
	fMaxSPL = numpy.max(npaTestSPLs)
	fMinSPL = numpy.min(npaTestSPLs)
	
	fMaxDeviation = max( fMaxSPL - fSPL, fSPL - fMinSPL)
	
	k_spl = fMaxDeviation * k_spec_spl
	
	return k_spl + k_high + k_low

#calculate optimal fit of linear response

npaLower = numpy.logspace(numpy.log10(t_edge_low), numpy.log10(t_edge_low * 2), num=8)
npaHigher = numpy.logspace(numpy.log10(t_edge_high / 2), numpy.log10(t_edge_high), num=8)

fBest = float("inf")
fBestSPL = float("nan")
fBestLower = float("nan")
fBestHigher = float("nan")

for spl in range(t_spl - 10, t_spl + 10):
	for lower in npaLower:
		for higher in npaHigher:
			fCost = linearResponseCost(daMicSPLs[t_mic], spl, lower, higher)
			if fCost < fBest:
				fBest = fCost
				fBestSPL = spl
				fBestLower = lower
				fBestHigher = higher

#linearResponseCost(daMicSPLs[t_mic], fBestSPL, fBestLower, fBestHigher)
#print(dMatCosts)

k_total = fBest + dMatCosts["cost_total"]

print("costs: material", dMatCosts["cost_total"], "frequency response:", fBest, "total cost", k_total)


