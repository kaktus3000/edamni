#!/usr/python3
import numpy
import sys
import os
import configparser
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import scipy.signal

#xml support
import xml.etree.ElementTree as ET

#call external program
from subprocess import call

import material_costs

def runSimulation(strSimuInputFile, lstrSimuCommand, strPlotFile):
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

	t_edge_low_max = float(spl_cost_config.get("spl_targets", "t_edge_low_max"))

	print("run simulation: calling", lstrSimuCommand, "with", strSimuInputFile, "in", g_strDir)
	#call simulation with all the data
	print(lstrSimuCommand, strSimuInputFile, g_strDir)
	call(lstrSimuCommand + [strSimuInputFile], cwd=g_strDir)

	#collect results
	#parse simu output file
	tree = ET.parse(g_strSimuOutputFile)
	root = tree.getroot()
	
	nMics = len(root.findall("mic_spl") )
	
	daMicSPLs = dict()
	daSpeakerImpedances = dict()
	daSpeakerExcursions = dict()
	#periods for measuring spl and phase
	g_nMeasPeriods = 3
	#process signals
	for signal in root.findall("signal"):
		strSignalType = signal.attrib["type"]
		fSsignalFreq = float(signal.attrib["freq"])
		#print("Signal - type =", strSignalType, ", freq =", fSsignalFreq)
		#process outputs
		
		for mic_output in signal.findall("mic_output"):
			strMicID = mic_output.attrib["id"]
			strMicFile = mic_output.attrib["file"]
			
			#create spl information from time series
			npaData = numpy.loadtxt(g_strDir + strMicFile)

			npaStepResponse = numpy.transpose(npaData)[1]
			fTimeStep = npaData[0][0]

			npaImpulseResponse = numpy.ediff1d(npaStepResponse) / fTimeStep

			w,h = scipy.signal.freqz(npaImpulseResponse, worN=4096)
			
			w = w[10:int(len(w)*.9)]
			h = h[10:int(len(h)*.9)]

			npaFreqs = 1.1 * w/(fTimeStep * 2 * numpy.pi)
			npaSPLs  = (20 * numpy.log10(abs(h)) ) + 7
		
			daMicSPLs[strMicID] = numpy.transpose([npaFreqs, npaSPLs])
			
			nMics += 1
	
		for speaker_output in signal.findall("speaker_output"):
			strSpeakerId = speaker_output.attrib["id"]
			strSpeakerFile = speaker_output.attrib["file"]
	
		#video output is per frequency, no iteration needed.

	for micSPL in root.findall("mic_spl"):
		strMicSPLFile = micSPL.attrib["file"]
		strMicID = micSPL.attrib["id"]

		print("run simulation: SPL for", strMicID, ", file =", strMicSPLFile)
		daMicSPLs[strMicID] = numpy.loadtxt(g_strDir + strMicSPLFile)
		
	for speakerImpedance in root.findall("speaker_impedance"):
		strSpeakerImpedanceFile = speakerImpedance.attrib["file"]
		strSpeakerImpedanceID = speakerImpedance.attrib["id"]

		print("run simulation: SPL for", strSpeakerImpedanceID, ", file =", strSpeakerImpedanceFile)
		daSpeakerImpedances[strSpeakerImpedanceID] = numpy.loadtxt(g_strDir + strSpeakerImpedanceFile)
		
	for speakerExcursion in root.findall("speaker_excursion"):
		strSpeakerExcursionFile = speakerExcursion.attrib["file"]
		strSpeakerExcursionID = speakerExcursion.attrib["id"]

		print("run simulation: Excursion for", strSpeakerExcursionID, ", file =", strSpeakerExcursionFile)
		daSpeakerExcursions[strSpeakerExcursionID] = numpy.loadtxt(g_strDir + strSpeakerExcursionFile)

	if strPlotFile != "":
		# plot spl and impedance
		fig, axSPL = plt.subplots()
		axImpedance = axSPL.twinx()
		axExcursion = axSPL.twinx()
		
		fig.subplots_adjust(right=0.8)
		axExcursion.spines['right'].set_position(('axes', 1.15))
		
		plt.suptitle("Frequency Response Plot")

		axSPL.set_xscale("log", nonposx='clip')
		axImpedance.set_xscale("log", nonposx='clip')

		colors = cm.rainbow(numpy.linspace(0, 1, nMics))
		iMic = 0

		for strMicID in daMicSPLs.keys():
			npaFreqs = numpy.transpose(daMicSPLs[strMicID])[0]
			npaSPLs = numpy.transpose(daMicSPLs[strMicID])[1]
	
			axSPL.plot(npaFreqs, npaSPLs, "-", color = colors[iMic], label = strMicID)
			iMic += 1

		for strSpeakerImpedanceID in daSpeakerImpedances.keys():
			npaFreqs = numpy.transpose(daSpeakerImpedances[strSpeakerImpedanceID])[0]
			npaImpedances = numpy.transpose(daSpeakerImpedances[strSpeakerImpedanceID])[1]
	
			axImpedance.plot(npaFreqs, npaImpedances, "g-")
			
		for strSpeakerExcursionID in daSpeakerExcursions.keys():
			npaFreqs = numpy.transpose(daSpeakerExcursions[strSpeakerExcursionID])[0]
			npaExcursions = numpy.transpose(daSpeakerExcursions[strSpeakerExcursionID])[1]
	
			axExcursion.plot(npaFreqs, npaExcursions * 1000.0, "k-")

		axSPL.set_ylabel('SPL [dB]', color='b')
		axImpedance.set_ylabel('Impedance [ohms]', color='g')
		axExcursion.set_ylabel('Excursion [mm]', color='k')
		
		axSPL.set_xlabel('Frequency [Hz]')

		axSPL.legend(loc=4)
		axSPL.grid(which='both')

		print("run simulation: creating plot", strPlotFile)
		plt.savefig(strPlotFile)

		plt.close()
		
	t_mic = None

	for mic in daMicSPLs.keys():
		if t_mic == None:
			t_mic = mic
		if "spl_sum" in mic:
			t_mic = mic
			break

	#calculate optimal fit of linear response
	fBest = float("inf")
	fBestSPL = float("nan")
	fBestLower = float("nan")
	fBestDeviation = float("nan")
	
	fBestCostSPL = float("nan")
	fBestCostLower = float("nan")
	fBestCostDeviation = float("nan")
	
	npaSPLs = numpy.transpose(daMicSPLs[t_mic])[1]
	npaFreqs = numpy.transpose(daMicSPLs[t_mic])[0]
	
	for iLower in range(len(npaSPLs)):
		npaTestSPLs = npaSPLs[iLower:]
		fLower = npaFreqs[iLower]
		
		if fLower > t_edge_low_max:
			break
		
		k_low = numpy.log10(fLower / t_edge_low) * k_spec_decade
		k_low = max(k_low, 0)
		
		fMeanSPL = numpy.mean(npaTestSPLs)
		k_spl = abs(fMeanSPL - t_spl) * k_spec_spl
	
		npaDeviation = numpy.fabs(npaTestSPLs - fMeanSPL)
		fMaxDeviation = numpy.amax(npaDeviation)
		
		fRMSDeviation = numpy.sqrt(numpy.mean(numpy.square(npaDeviation) ) )
		
		fTotalDeviation = (4.0 * fMaxDeviation + fRMSDeviation) / 5
		
		k_linearity = fTotalDeviation * k_spec_linearity
		
		fCost = k_low + k_spl + k_linearity
		
		if fCost <= fBest:
			fBest = fCost
			fBestSPL = fMeanSPL
			fBestLower = fLower
			fBestDeviation = fTotalDeviation
			
			fBestCostSPL = k_spl
			fBestCostLower = k_low
			fBestCostDeviation = k_linearity
		
	
	k_total = fBest + dMatCosts["cost_total"]

	print("run simulation: total cost", k_total)
	
	strDesignReportFile = g_strSimuOutputFile + "_design_report.txt"
	
	hDesignReportFile = open(strDesignReportFile, "wt")
	hDesignReportFile.write("=== DESIGN REPORT ===\n\n")
	
	hDesignReportFile.write("Resonator Volume\t" + str(dMatCosts["air_volume"]*1e3) + "\tl\n")
	hDesignReportFile.write("Resonator Length\t" + str(dMatCosts["length"]) + "\tm\n")
	hDesignReportFile.write("Resonator Surface Area\t" + str(dMatCosts["surface_area"]) + "\tm^2\n")
	hDesignReportFile.write("Panel Thickness\t" + str(dMatCosts["panel_thickness"]*1e3) + "\tmm\n")

	hDesignReportFile.write("Enclosure Cost\t" + str(dMatCosts["cost_enclosure"]) + "\t$\n")
	hDesignReportFile.write("Resonator Surface Cost\t" + str(dMatCosts["cost_surface"]) + "\t$\n")
	hDesignReportFile.write("Resonator Damping Cost\t" + str(dMatCosts["cost_damping"]) + "\t$\n")
	
	hDesignReportFile.write("Resonator Total Cost\t" + str(dMatCosts["cost_total"]) + "\t$\n")
	
	hDesignReportFile.write("Lower Edge\t" + str(fBestLower) + "\tHz\t" + str(k_spec_decade) + "\t$/decade\t" + str(fBestCostLower) + "$\t" + "target\t" + str(t_edge_low) + "\n")
	hDesignReportFile.write("Mean SPL\t" + str(fBestSPL) + "\tdB\t" + str(k_spec_spl) + "\t$/dB\t" + str(fBestCostSPL) + "$\t" + "target\t" + str(t_spl) + "\n")
	hDesignReportFile.write("Max SPL Deviation\t" + str(fBestDeviation) + "\tdB\t" + str(k_spec_linearity) + "\t$/dB\t" + str(fBestCostDeviation) + "$\n")
	
	hDesignReportFile.write("SPL Total Cost\t" + str(fBest) + "\t$\n")
	
	hDesignReportFile.write("Design Total Cost\t" + str(k_total) + "\t$\n")
	
	hDesignReportFile.close()
	
	#hDesignReportFile.write("Mean SPL\t" + str(fMeanSPL) + "\t$\n")
	
	return k_total

if __name__ == "__main__":
	strSimuInputFile = sys.argv[1]
	strPlotFile = sys.argv[2]
	lstrSimuCommand = sys.argv[3:]
	
	runSimulation(strSimuInputFile, lstrSimuCommand, strPlotFile)
	
