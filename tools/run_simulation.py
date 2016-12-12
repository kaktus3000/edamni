#!/usr/python3
import numpy
import sys
import os
import configparser
import matplotlib.pyplot as plt
import matplotlib.cm as cm

#xml support
import xml.etree.ElementTree as ET

#call external program
from subprocess import call

import material_costs

def runSimulation(strSimuInputFile, lstrSimuCommand):
	print("run simulation: os dir", os.getcwd() )

	strOSDir = os.path.dirname(strSimuInputFile)

	if strOSDir=="":
		strOSDir = "."

	g_strDir = strOSDir + "/"

	print("run simulation: run dir", g_strDir)

	#get job data
	config = configparser.ConfigParser()

	config.read(strSimuInputFile)
	g_strSimuOutputFile = g_strDir + config.get("general", "output_file")
	g_strElementFile = g_strDir + config.get("general", "element_file")

	# calculate costs for this design
	dMatCosts = material_costs.get_material_costs(g_strElementFile)

	# get cost for optimization
	spl_cost_config = configparser.ConfigParser()

	spl_cost_config.read("spl_cost.ini")

	# specific cost for missing one decade
	k_spec_decade = float(spl_cost_config.get("spl_costs", "k_spec_decade"))
	# specific cost for one dB lower flat response
	k_spec_spl = float(spl_cost_config.get("spl_costs", "k_spec_spl"))
	# specific cost for one dB spl deviation
	k_spec_linearity = float(spl_cost_config.get("spl_costs", "k_spec_linearity"))

	# optimization targets
	# target spl in transmission range
	t_spl = int(spl_cost_config.get("spl_targets", "t_spl"))
	# upper and lower edge frequencies [Hz]
	t_edge_low = float(spl_cost_config.get("spl_targets", "t_edge_low"))
	t_edge_high = float(spl_cost_config.get("spl_targets", "t_edge_high"))

	print("run simulation: calling", lstrSimuCommand, "with", strSimuInputFile, "in", g_strDir)
	#call simulation with all the data
	call(lstrSimuCommand + [strSimuInputFile], cwd=g_strDir)

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
		#print("Signal - type =", strSignalType, ", freq =", fSsignalFreq)
		#process outputs
		for mic_output in signal.findall("mic_output"):
			strMicId = mic_output.attrib["id"]
			strMicFile = mic_output.attrib["file"]
		
	
		for speaker_output in signal.findall("speaker_output"):
			strSpeakerId = speaker_output.attrib["id"]
			strSpeakerFile = speaker_output.attrib["file"]
	
		#video output is per frequency, no iteration needed.

	# plot spl and impedance
	fig, ax1 = plt.subplots()
	ax2 = ax1.twinx()
	plt.suptitle("Frequency Response Plot")

	ax1.set_xscale("log", nonposx='clip')
	ax2.set_xscale("log", nonposx='clip')

	nMics = len(root.findall("mic_spl") )

	colors = cm.rainbow(numpy.linspace(0, 1, nMics))
	iMic = 0

	for micSPL in root.findall("mic_spl"):
		strMicSPLFile = micSPL.attrib["file"]
		strMicID = micSPL.attrib["id"]

		print("run simulation: SPL for", strMicID, ", file =", strMicSPLFile)
	
		daMicSPLs[strMicID] = numpy.loadtxt(g_strDir + strMicSPLFile)
	
		npaFreqs = numpy.transpose(daMicSPLs[strMicID])[0]
		npaSPLs = numpy.transpose(daMicSPLs[strMicID])[1]
	
		ax1.plot(npaFreqs, npaSPLs, "-", color = colors[iMic], label = strMicID)
	
		iMic += 1

	for speakerImpedance in root.findall("speaker_impedance"):
		strSpeakerImpedanceFile = speakerImpedance.attrib["file"]
		strSpeakerImpedanceID = speakerImpedance.attrib["id"]

		print("run simulation: SPL for", strSpeakerImpedanceID, ", file =", strSpeakerImpedanceFile)
	
		daSpeakerImpedances[strSpeakerImpedanceID] = numpy.loadtxt(g_strDir + strSpeakerImpedanceFile)
	
		npaFreqs = numpy.transpose(daSpeakerImpedances[strSpeakerImpedanceID])[0]
		npaImpedances = numpy.transpose(daSpeakerImpedances[strSpeakerImpedanceID])[1]
	
		ax2.plot(npaFreqs, npaImpedances, "g-")

	ax1.set_ylabel('SPL [dB]', color='b')
	ax2.set_ylabel('Impedance [ohms]', color='g')
	ax1.set_xlabel('Frequency [Hz]')

	ax1.legend(loc=2)
	ax1.grid(which='both')

	strPlotPath = g_strDir + "spl.png"
	print("run simulation: creating plot", strPlotPath)
	plt.savefig(strPlotPath)

	plt.close()

	t_mic = None

	for mic in daMicSPLs.keys():
		if t_mic == None:
			t_mic = mic
		if "spl_sum" in mic:
			t_mic = mic
			break

	#calculate cost for a linear response fit
	def linearResponseCost(npaSPL, fSPL, fLowEdge, fHighEdge):
		#edge cost is easy
		k_high = numpy.log10(t_edge_high / fHighEdge) * k_spec_decade
		k_low = numpy.log10(fLowEdge / t_edge_low) * k_spec_decade

		k_high = max(0, k_high)
		k_low = max(0, k_low)
	
		#check linearity
		npaTransposed = numpy.transpose(npaSPL)
		npaFreqs = npaTransposed[0]
		npaSPLs = npaTransposed[1]
	
		npaFreqMask = (npaFreqs > fLowEdge) * (npaFreqs < fHighEdge)
	
		npaTestSPLs = npaSPLs[numpy.flatnonzero(npaFreqMask)]
	
		fMaxSPL = numpy.amax(npaTestSPLs)
		fMinSPL = numpy.amin(npaTestSPLs)
	
		fMaxDeviation = max( abs(fMaxSPL - fSPL), abs(fSPL - fMinSPL) )
	
		k_linearity = fMaxDeviation * k_spec_linearity
	
		k_spl = abs(fSPL - t_spl) * k_spec_spl
	
		return k_spl + k_high + k_low + k_linearity

	#calculate optimal fit of linear response

	npaLower = numpy.logspace(numpy.log10(t_edge_low), numpy.log10(t_edge_low * 2), num=8)
	npaHigher = numpy.logspace(numpy.log10(t_edge_high / 2), numpy.log10(t_edge_high), num=8)

	fBest = float("inf")
	fBestSPL = float("nan")
	fBestLower = float("nan")
	fBestHigher = float("nan")

	'''
	for spl in range(t_spl - 10, t_spl + 10):
		for lower in npaLower:
			for higher in npaHigher:
				fCost = linearResponseCost(daMicSPLs[t_mic], spl, lower, higher)
				if fCost <= fBest:
					fBest = fCost
					fBestSPL = spl
					fBestLower = lower
					fBestHigher = higher

	#linearResponseCost(daMicSPLs[t_mic], fBestSPL, fBestLower, fBestHigher)
	#print(dMatCosts)
	'''

	npaSPLs = numpy.transpose(daMicSPLs[t_mic])[1]
	
	fMeanSPL = numpy.mean(npaSPLs)
	k_spl = abs(fMeanSPL - t_spl) * k_spec_spl
	
	npaDeviation = numpy.fabs(npaSPLs - t_spl)
	fMaxDeviation = numpy.amax(npaDeviation)
	k_linearity = fMaxDeviation * k_spec_linearity
	
	print("run simulation: mean spl", fMeanSPL, "max deviation", fMaxDeviation)
	
	fBest = k_spl + k_linearity

	k_total = fBest + dMatCosts["cost_total"]

	print("run simulation: material cost", dMatCosts["cost_total"], "; panel thickness", dMatCosts["panel_thickness"], "cube edge length", dMatCosts["edge_length"])

#	print("run simulation: frequency response cost (", t_mic, ")", fBest, "lower edge", fBestLower, "upper edge", fBestHigher, "mean spl", fBestSPL)


	print("run simulation: total cost", k_total)
	
	return k_total

if __name__ == "__main__":
	strSimuInputFile = sys.argv[1]
	lstrSimuCommand = sys.argv[2:]
	
	runSimulation(strSimuInputFile, lstrSimuCommand)
	
